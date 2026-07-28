import cytoscape, { Core, ElementDefinition, StylesheetStyle } from 'cytoscape';

import { parseCyEdgeId, parseCyNodeId } from './graph-model';

export interface GraphCyCallbacks {
  onNodeTap: (nodeId: number) => void;
  onEdgeTap: (edgeId: number) => void;
  onBackgroundTap: () => void;
  onNodeDragFree: (nodeId: number, position: { x: number; y: number }) => void;
}

/**
 * Create a Cytoscape instance for a relationship web and wire up tap/drag
 * callbacks. Zone handling (runOutsideAngular / zone.run) stays in the caller.
 */
export function createGraphCytoscape(
  container: HTMLElement,
  elements: ElementDefinition[],
  style: StylesheetStyle[],
  callbacks: GraphCyCallbacks,
): Core {
  const cy = cytoscape({
    container,
    elements,
    minZoom: 0.2,
    maxZoom: 2.5,
    wheelSensitivity: 0.25,
    style,
    layout: { name: 'preset' },
  });

  cy.on('tap', 'node', (event) => {
    callbacks.onNodeTap(parseCyNodeId(event.target.id()));
  });

  cy.on('tap', 'edge', (event) => {
    callbacks.onEdgeTap(parseCyEdgeId(event.target.id()));
  });

  cy.on('tap', (event) => {
    if (event.target === cy) {
      callbacks.onBackgroundTap();
    }
  });

  cy.on('dragfree', 'node', (event) => {
    const nodeId = parseCyNodeId(event.target.id());
    if (Number.isNaN(nodeId)) {
      return;
    }
    callbacks.onNodeDragFree(nodeId, event.target.position());
  });

  return cy;
}
