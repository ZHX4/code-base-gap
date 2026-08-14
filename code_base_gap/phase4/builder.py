"""Build a program knowledge graph from the Phase 3 semantic index."""
from __future__ import annotations

from typing import Iterable

from code_base_gap.phase3.models import ParsedFile, SemanticIndex

from .ids import edge_id, stable_id
from .models import GraphEdge, GraphNode, ProgramKnowledgeGraph
from .resolver import resolve_import, resolve_reference, unique_symbols_by_name


def _span_props(span: object) -> dict[str, object]:
    return {
        "start_byte": int(getattr(span, "start_byte")),
        "end_byte": int(getattr(span, "end_byte")),
        "start_line": int(getattr(getattr(span, "start"), "line")),
        "start_column": int(getattr(getattr(span, "start"), "column")),
        "end_line": int(getattr(getattr(span, "end"), "line")),
        "end_column": int(getattr(getattr(span, "end"), "column")),
    }


def _file_node(parsed: ParsedFile) -> GraphNode:
    return GraphNode(
        stable_id("file", parsed.path, parsed.source_sha256),
        "file",
        parsed.path,
        {
            "path": parsed.path,
            "language": parsed.language,
            "source_sha256": parsed.source_sha256,
            "byte_length": parsed.byte_length,
            "has_errors": parsed.has_errors,
            "error_count": parsed.error_count,
        },
    )


def _module_node(parsed: ParsedFile) -> GraphNode:
    module_name = parsed.path.rsplit(".", 1)[0].replace("/", ".")
    return GraphNode(
        stable_id("module", parsed.path),
        "module",
        module_name,
        {"path": parsed.path, "language": parsed.language, "module_name": module_name},
    )


def build_program_graph(index: SemanticIndex) -> ProgramKnowledgeGraph:
    graph = ProgramKnowledgeGraph(repository_revision=index.repository_revision)
    repository_id = stable_id("repository", index.repository_revision or "unknown")
    graph.add_node(GraphNode(repository_id, "repository", "repository", {"revision": index.repository_revision}))

    file_nodes: dict[str, GraphNode] = {}
    module_nodes: dict[str, GraphNode] = {}
    symbol_nodes: dict[tuple[str, str], GraphNode] = {}
    files_by_path = {parsed.path: parsed for parsed in index.files}
    files_set = set(files_by_path)

    for parsed in index.files:
        file_node = _file_node(parsed)
        module_node = _module_node(parsed)
        file_nodes[parsed.path] = file_node
        module_nodes[parsed.path] = module_node
        graph.add_node(file_node)
        graph.add_node(module_node)
        graph.add_edge(GraphEdge(edge_id("CONTAINS", repository_id, file_node.node_id), repository_id, file_node.node_id, "CONTAINS"))
        graph.add_edge(GraphEdge(edge_id("CONTAINS", file_node.node_id, module_node.node_id), file_node.node_id, module_node.node_id, "CONTAINS"))
        graph.add_edge(GraphEdge(edge_id("LOCATED_IN", module_node.node_id, file_node.node_id), module_node.node_id, file_node.node_id, "LOCATED_IN"))

        for symbol in parsed.symbols:
            node = GraphNode(
                stable_id("symbol", parsed.source_sha256, symbol.symbol_id),
                "symbol",
                symbol.name,
                {
                    "symbol_id": symbol.symbol_id,
                    "kind": symbol.kind,
                    "path": parsed.path,
                    "language": parsed.language,
                    "exported": symbol.exported,
                    "signature": symbol.signature,
                    "span": _span_props(symbol.span),
                    "name_span": _span_props(symbol.name_span),
                },
            )
            symbol_nodes[(parsed.path, symbol.symbol_id)] = node
            graph.add_node(node)
            graph.add_edge(GraphEdge(edge_id("DECLARES", file_node.node_id, node.node_id), file_node.node_id, node.node_id, "DECLARES"))
            if symbol.parent_symbol_id:
                parent = symbol_nodes.get((parsed.path, symbol.parent_symbol_id))
                if parent:
                    graph.add_edge(GraphEdge(edge_id("CONTAINS", parent.node_id, node.node_id), parent.node_id, node.node_id, "CONTAINS"))

        for symbol in parsed.exports:
            target = symbol_nodes.get((parsed.path, symbol.symbol_id))
            if target:
                graph.add_edge(GraphEdge(edge_id("EXPORTS", file_node.node_id, target.node_id), file_node.node_id, target.node_id, "EXPORTS"))

        for endpoint in parsed.endpoints:
            node = GraphNode(
                stable_id("endpoint", parsed.source_sha256, endpoint.span.start_byte, endpoint.method, endpoint.path),
                "endpoint",
                endpoint.path or "<dynamic-endpoint>",
                {"framework": endpoint.framework, "method": endpoint.method, "path": endpoint.path, "handler_hint": endpoint.handler_hint, "span": _span_props(endpoint.span)},
            )
            graph.add_node(node)
            graph.add_edge(GraphEdge(edge_id("EXPOSES", file_node.node_id, node.node_id), file_node.node_id, node.node_id, "EXPOSES"))

        for query in parsed.queries:
            node = GraphNode(
                stable_id("query", parsed.source_sha256, query.span.start_byte, query.query_kind),
                "query",
                query.query_kind,
                {"query_kind": query.query_kind, "text": query.text, "span": _span_props(query.span)},
            )
            graph.add_node(node)
            owner = symbol_nodes.get((parsed.path, query.context_symbol_id)) if query.context_symbol_id else None
            source = owner.node_id if owner else file_node.node_id
            graph.add_edge(GraphEdge(edge_id("EXECUTES_QUERY", source, node.node_id), source, node.node_id, "EXECUTES_QUERY"))

        for config in parsed.configs:
            node = GraphNode(
                stable_id("config", parsed.source_sha256, config.span.start_byte, config.key),
                "config",
                config.key,
                {"key": config.key, "value_kind": config.value_kind, "span": _span_props(config.span)},
            )
            graph.add_node(node)
            graph.add_edge(GraphEdge(edge_id("USES_CONFIG", file_node.node_id, node.node_id), file_node.node_id, node.node_id, "USES_CONFIG"))

        for integration in parsed.integrations:
            node = GraphNode(
                stable_id("integration", integration.integration, integration.kind),
                "integration",
                integration.integration,
                {"integration": integration.integration, "kind": integration.kind},
            )
            graph.add_node(node)
            graph.add_edge(GraphEdge(edge_id("INTEGRATES_WITH", file_node.node_id, node.node_id), file_node.node_id, node.node_id, "INTEGRATES_WITH", {"span": _span_props(integration.span)}))

        for test in parsed.tests:
            node = GraphNode(
                stable_id("test", parsed.source_sha256, test.span.start_byte, test.name),
                "test",
                test.name or "<anonymous-test>",
                {"framework": test.framework, "name": test.name, "span": _span_props(test.span)},
            )
            graph.add_node(node)
            graph.add_edge(GraphEdge(edge_id("CONTAINS", file_node.node_id, node.node_id), file_node.node_id, node.node_id, "CONTAINS"))

    global_by_name = unique_symbols_by_name(index.files)

    for parsed in index.files:
        file_node = file_nodes[parsed.path]
        for import_record in parsed.imports:
            target_path = resolve_import(parsed.path, import_record, files_set)
            if target_path is not None:
                target_module = module_nodes[target_path]
                graph.add_edge(GraphEdge(
                    edge_id("IMPORTS", file_node.node_id, target_module.node_id, import_record.span.start_byte),
                    file_node.node_id,
                    target_module.node_id,
                    "IMPORTS",
                    {"source": import_record.source, "kind": import_record.kind, "span": _span_props(import_record.span)},
                ))
            else:
                external = GraphNode(
                    stable_id("external_module", import_record.source),
                    "external_module",
                    import_record.source,
                    {"module": import_record.source},
                )
                graph.add_node(external)
                graph.add_edge(GraphEdge(
                    edge_id("IMPORTS", file_node.node_id, external.node_id, import_record.span.start_byte),
                    file_node.node_id,
                    external.node_id,
                    "IMPORTS",
                    {"source": import_record.source, "kind": import_record.kind, "resolved": False, "span": _span_props(import_record.span)},
                ))

        local_symbols = list(parsed.symbols)
        for reference in parsed.references:
            resolved = resolve_reference(parsed, reference, local_symbols, global_by_name)
            if resolved is None:
                continue
            target_path, target_symbol = resolved
            target = symbol_nodes.get((target_path, target_symbol.symbol_id))
            if target is None:
                continue
            context = symbol_nodes.get((parsed.path, reference.context_symbol_id)) if reference.context_symbol_id else None
            source = context.node_id if context else file_node.node_id
            graph.add_edge(GraphEdge(
                edge_id("RESOLVES_TO", source, target.node_id, reference.span.start_byte, reference.name),
                source,
                target.node_id,
                "RESOLVES_TO",
                {"name": reference.name, "span": _span_props(reference.span), "resolution": "unique"},
            ))

        for test in parsed.tests:
            test_node_id = stable_id("test", parsed.source_sha256, test.span.start_byte, test.name)
            candidate_names = []
            if test.name:
                candidate_names.append(test.name)
                if test.name.startswith("test_"):
                    candidate_names.append(test.name[5:])
            candidates = [
                (path, symbol) for path, symbol in global_by_name.get(candidate_names[0], [])
            ] if candidate_names else []
            if len(candidates) != 1 and len(candidate_names) > 1:
                candidates = [
                    (path, symbol) for name in candidate_names[1:] for path, symbol in global_by_name.get(name, [])
                ]
            if len(candidates) == 1:
                target_path, target_symbol = candidates[0]
                target = symbol_nodes.get((target_path, target_symbol.symbol_id))
                if target and test_node_id in graph.nodes:
                    graph.add_edge(GraphEdge(
                        edge_id("TESTS", test_node_id, target.node_id),
                        test_node_id,
                        target.node_id,
                        "TESTS",
                        {"resolution": "name-heuristic"},
                    ))

    graph.validate_and_normalize()
    return graph
