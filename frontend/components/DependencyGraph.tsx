"use client";

import { useMemo } from "react";
import {
  ReactFlow,
  Background,
  Handle,
  Position,
  type Node,
  type Edge,
} from "@xyflow/react";
import dagre from "@dagrejs/dagre";
import "@xyflow/react/dist/style.css";
import type { GraphResponse } from "@/lib/types";
import { severityColor } from "@/lib/utils";

interface DependencyGraphProps {
  data: GraphResponse;
}

const NODE_WIDTH = 170;
const NODE_HEIGHT = 36;
const MAX_IN = 2;
const MAX_OUT = 3;

function buildGraph(
  rawNodes: GraphResponse["nodes"],
  rawEdges: GraphResponse["edges"]
) {
  const nodeIds = new Set(rawNodes.map((n) => n.id));
  const nodeMap = new Map(rawNodes.map((n) => [n.id, n]));

  const validEdges = rawEdges.filter(
    (e) => nodeIds.has(e.source) && nodeIds.has(e.target)
  );

  const inCount: Record<string, number> = {};
  const outCount: Record<string, number> = {};
  const prunedEdges: GraphResponse["edges"] = [];

  for (const e of validEdges) {
    const ic = inCount[e.target] || 0;
    const oc = outCount[e.source] || 0;
    if (ic < MAX_IN && oc < MAX_OUT) {
      prunedEdges.push(e);
      inCount[e.target] = ic + 1;
      outCount[e.source] = oc + 1;
    }
  }

  const connectedIds = new Set<string>();
  for (const e of prunedEdges) {
    connectedIds.add(e.source);
    connectedIds.add(e.target);
  }

  const connectedNodes = rawNodes.filter((n) => connectedIds.has(n.id));
  const orphanNodes = rawNodes.filter((n) => !connectedIds.has(n.id));

  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: "TB", nodesep: 30, ranksep: 50, marginx: 20, marginy: 20 });

  connectedNodes.forEach((n) =>
    g.setNode(n.id, { width: NODE_WIDTH, height: NODE_HEIGHT })
  );
  prunedEdges.forEach((e) => g.setEdge(e.source, e.target));
  dagre.layout(g);

  const nodes: Node[] = connectedNodes.map((n) => {
    const pos = g.node(n.id);
    return {
      id: n.id,
      position: { x: pos.x - NODE_WIDTH / 2, y: pos.y - NODE_HEIGHT / 2 },
      data: n.data,
      type: "conceptNode",
      draggable: false,
      selectable: false,
      connectable: false,
    };
  });

  const edges: Edge[] = prunedEdges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    type: "default",
    style: { stroke: "#6366f1", strokeWidth: 1.5, opacity: 0.5 },
    markerEnd: { type: "arrowclosed" as any, color: "#6366f1", width: 12, height: 12 },
  }));

  return { nodes, edges, orphans: orphanNodes };
}

function ConceptNode({ data }: { data: any }) {
  const dotColor = severityColor(data.severity);

  return (
    <>
      <Handle type="target" position={Position.Top} className="!bg-transparent !w-1 !h-1 !border-0 !min-w-0 !min-h-0" />
      <div className="rounded-md border border-[var(--color-border)] bg-[var(--color-card)] px-3 py-1.5" style={{ width: NODE_WIDTH }}>
        <div className="flex items-center gap-2">
          <div className={`h-2 w-2 shrink-0 rounded-full ${dotColor}`} />
          <span className="text-[11px] font-medium text-[var(--color-foreground)] truncate">
            {data.label}
          </span>
        </div>
      </div>
      <Handle type="source" position={Position.Bottom} className="!bg-transparent !w-1 !h-1 !border-0 !min-w-0 !min-h-0" />
    </>
  );
}

const nodeTypes = { conceptNode: ConceptNode };

export default function DependencyGraph({ data }: DependencyGraphProps) {
  const { nodes, edges, orphans } = useMemo(
    () => buildGraph(data.nodes, data.edges),
    [data]
  );

  if (data.nodes.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center text-[var(--color-muted)]">
        No dependency data available.
      </div>
    );
  }

  if (nodes.length === 0) {
    return (
      <div className="space-y-3">
        <p className="text-sm text-[var(--color-muted)]">
          No dependencies found between concepts.
        </p>
        <div className="flex flex-wrap gap-2">
          {data.nodes.map((n) => (
            <span
              key={n.id}
              className="inline-flex items-center gap-1.5 rounded-md border border-[var(--color-border)] bg-[var(--color-card)] px-2.5 py-1 text-xs"
            >
              <span className={`h-1.5 w-1.5 rounded-full ${severityColor(n.data.severity)}`} />
              {n.data.label}
            </span>
          ))}
        </div>
      </div>
    );
  }

  const height = Math.min(500, Math.max(300, nodes.length * 45));

  return (
    <div className="space-y-4">
      <div
        className="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-background)]"
        style={{ height }}
      >
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.15 }}
          nodesDraggable={false}
          nodesConnectable={false}
          elementsSelectable={false}
          panOnDrag={true}
          zoomOnScroll={true}
          panOnScroll={false}
          preventScrolling={false}
        >
          <Background color="#1e293b" gap={20} />
        </ReactFlow>
      </div>

      {orphans.length > 0 && (
        <div>
          <p className="mb-2 text-xs text-[var(--color-muted)]">
            Other concepts (no dependencies detected):
          </p>
          <div className="flex flex-wrap gap-1.5">
            {orphans.map((n) => (
              <span
                key={n.id}
                className="inline-flex items-center gap-1.5 rounded-md border border-[var(--color-border)] bg-[var(--color-card)] px-2 py-0.5 text-[11px]"
              >
                <span className={`h-1.5 w-1.5 rounded-full ${severityColor(n.data.severity)}`} />
                {n.data.label}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
