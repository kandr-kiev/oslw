/**
 * Graph component — візуалізація графа знань.
 * 
 * Використовує Cytoscape для відображення:
 * - Нод (сторінок, концептів)
 * - Ребер (зв'язків між ними)
 * - Інтерактивного масштабування та перетягування
 */

import { useState, useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';
import dagre from 'cytoscape-dagre';
import { api } from '../services/api';

cytoscape.use(dagre);

function Graph() {
  const graphRef = useRef(null);
  const [cy, setCy] = useState(null);
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadGraph();
  }, []);

  const loadGraph = async () => {
    try {
      setLoading(true);
      const data = await api.getGraph();
      setGraphData(data);
      setError(null);
    } catch (err) {
      setError(err.message || 'Не вдалося завантажити граф');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!graphRef.current || !graphData) return;

    // Initialize Cytoscape
    const instance = cytoscape({
      container: graphRef.current,
      elements: graphData.elements || [],
      style: [
        {
          selector: 'node',
          style: {
            'background-color': '#3b82f6',
            'label': 'data(label)',
            'color': '#fff',
            'text-valign': 'center',
            'text-halign': 'center',
            'text-outline-width': 2,
            'text-outline-color': '#1f2937',
            'width': 60,
            'height': 60,
          },
        },
        {
          selector: 'edge',
          style: {
            'width': 2,
            'line-color': '#6b7280',
            'target-arrow-color': '#6b7280',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
          },
        },
      ],
      layout: {
        name: 'dagre',
        rankDir: 'BT',
        nodeSep: 50,
        edgeSep: 10,
      },
      minZoom: 0.3,
      maxZoom: 3,
    });

    setCy(instance);

    return () => {
      instance.destroy();
    };
  }, [graphData]);

  const handleRefresh = async () => {
    await api.generateGraph();
    await loadGraph();
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold">🌐 Граф знань</h2>
        <button
          onClick={handleRefresh}
          className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg"
        >
          🔄 Оновити граф
        </button>
      </div>

      {loading && (
        <div className="text-center py-8 text-gray-400">Завантаження графу...</div>
      )}

      {error && (
        <div className="bg-red-900/50 border border-red-700 rounded-lg p-4 text-red-300">
          {error}
        </div>
      )}

      {graphData && !loading && !error && (
        <>
          <div className="text-gray-400 text-sm">
            Нод: {graphData.total || 0} • Ребер: {graphData.edges?.length || 0}
          </div>
          <div
            ref={graphRef}
            className="w-full h-[600px] bg-gray-800 rounded-lg border border-gray-700"
          />
        </>
      )}

      {!graphData && !loading && !error && (
        <div className="text-center py-8 text-gray-400">
          Граф порожній. Спробуйте згенерувати знову.
        </div>
      )}
    </div>
  );
}

export default Graph;
