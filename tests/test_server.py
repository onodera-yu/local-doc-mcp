from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

from local_doc_mcp.indexer import build_index
from local_doc_mcp.chunker import chunk_documents
from local_doc_mcp.parser import parse_file


@pytest.fixture(scope="module")
def _build_test_index(tmp_path_factory):
    """テスト用インデックスをサーバーのデフォルトパスに構築する。"""
    # server.py の DB_PATH と同じ場所にインデックスを構築
    db_path = Path(__file__).resolve().parent.parent / "lancedb_data"
    fixtures_dir = Path(__file__).parent / "fixtures"

    docs = parse_file(fixtures_dir / "sample.txt")
    chunks = chunk_documents(docs)
    build_index(db_path, chunks)
    yield
    # テスト後にインデックスを再構築（元のknowledgeデータがあれば）
    knowledge_dir = Path(__file__).resolve().parent.parent / "knowledge"
    if knowledge_dir.exists():
        all_docs = []
        for f in knowledge_dir.rglob("*"):
            if f.is_file() and not f.name.startswith("."):
                try:
                    all_docs.extend(parse_file(f))
                except ValueError:
                    pass
        if all_docs:
            build_index(db_path, chunk_documents(all_docs))


@pytest.fixture(scope="module")
def server_params():
    return StdioServerParameters(
        command="uv",
        args=["run", "local-doc-mcp"],
    )


class TestMcpServer:
    @pytest.mark.usefixtures("_build_test_index")
    async def test_list_tools(self, server_params):
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                tool_names = [t.name for t in tools.tools]
                assert "search_docs" in tool_names
                assert "analyze_attachment" in tool_names

    @pytest.mark.usefixtures("_build_test_index")
    async def test_search_docs(self, server_params):
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "search_docs", {"query": "テスト", "top_k": 3}
                )
                assert len(result.content) >= 1
                data = json.loads(result.content[0].text)
                assert "text" in data
                assert "source" in data

    @pytest.mark.usefixtures("_build_test_index")
    async def test_analyze_attachment_success(self, server_params):
        fixtures_dir = Path(__file__).parent / "fixtures"
        txt_path = str(fixtures_dir / "sample.txt")

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "analyze_attachment", {"file_path": txt_path}
                )
                data = json.loads(result.content[0].text)
                assert data["file_type"] == "txt"
                assert data["file_name"] == "sample.txt"
                assert len(data["sections"]) >= 1

    async def test_analyze_attachment_not_found(self, server_params):
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "analyze_attachment", {"file_path": "/nonexistent/file.pdf"}
                )
                data = json.loads(result.content[0].text)
                assert "error" in data

    async def test_analyze_attachment_unsupported(self, server_params, tmp_path):
        unsupported = tmp_path / "test.xyz"
        unsupported.write_text("dummy")

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "analyze_attachment", {"file_path": str(unsupported)}
                )
                data = json.loads(result.content[0].text)
                assert "error" in data
