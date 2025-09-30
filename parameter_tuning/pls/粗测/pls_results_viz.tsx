import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ScatterChart, Scatter } from 'recharts';

export default function PLSResultsViz() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const content = await window.fs.readFile('pls_grid_search_results.csv', { encoding: 'utf8' });
        const lines = content.trim().split('\n');
        const headers = lines[0].split(',');
        
        const parsed = lines.slice(1).map(line => {
          const values = line.split(',');
          return {
            n_components: parseInt(values[5]),
            scale: values[6] === 'True',
            mean_score: parseFloat(values[13]),
            std_score: parseFloat(values[14]),
            rank: parseInt(values[15])
          };
        });
        
        setData(parsed);
        setLoading(false);
      } catch (error) {
        console.error('Error loading data:', error);
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) return <div className="p-8">加载中...</div>;

  // 按n_components分组计算平均R²
  const componentScores = {};
  data.forEach(row => {
    if (!componentScores[row.n_components]) {
      componentScores[row.n_components] = [];
    }
    componentScores[row.n_components].push(row.mean_score);
  });

  const lineData = Object.keys(componentScores)
    .map(nc => ({
      n_components: parseInt(nc),
      avg_score: componentScores[nc].reduce((a, b) => a + b) / componentScores[nc].length,
      max_score: Math.max(...componentScores[nc])
    }))
    .sort((a, b) => a.n_components - b.n_components);

  // Top 10
  const top10 = [...data]
    .sort((a, b) => b.mean_score - a.mean_score)
    .slice(0, 10);

  return (
    <div className="p-6 space-y-6 bg-gray-50">
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-2xl font-bold mb-2">PLS回归参数搜索结果</h2>
        <p className="text-gray-600">共测试 {data.length} 种参数组合</p>
      </div>

      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-xl font-bold mb-4">R²得分 vs 主成分数量</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={lineData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="n_components" label={{ value: '主成分数量', position: 'insideBottom', offset: -5 }} />
            <YAxis label={{ value: 'R² 得分', angle: -90, position: 'insideLeft' }} />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="avg_score" stroke="#8884d8" name="平均R²" strokeWidth={2} />
            <Line type="monotone" dataKey="max_score" stroke="#82ca9d" name="最高R²" strokeWidth={2} strokeDasharray="5 5" />
          </LineChart>
        </ResponsiveContainer>
        <p className="text-sm text-gray-600 mt-2">📊 最佳主成分数量为 <strong>4</strong>，达到峰值后性能下降</p>
      </div>

      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-xl font-bold mb-4">Top 10 最佳参数组合</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">排名</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">主成分数</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Scale</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">R²得分</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">标准差</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {top10.map((row, i) => (
                <tr key={i} className={i === 0 ? 'bg-green-50' : ''}>
                  <td className="px-4 py-3 whitespace-nowrap text-sm font-medium">{i + 1}</td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm">{row.n_components}</td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm">{row.scale ? '✓' : '✗'}</td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm font-semibold">{row.mean_score.toFixed(4)}</td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">±{row.std_score.toFixed(4)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-xl font-bold mb-4">🎯 关键发现</h3>
        <div className="space-y-3 text-gray-700">
          <div className="flex items-start">
            <span className="text-2xl mr-3">1️⃣</span>
            <p><strong>最佳参数</strong>：n_components=4, scale=False, max_iter=500</p>
          </div>
          <div className="flex items-start">
            <span className="text-2xl mr-3">2️⃣</span>
            <p><strong>模型性能</strong>：R² = 0.5388，能解释约54%的方差</p>
          </div>
          <div className="flex items-start">
            <span className="text-2xl mr-3">3️⃣</span>
            <p><strong>参数影响</strong>：
              <br/>• max_iter (500 vs 1000)：无差异，500次迭代已收敛
              <br/>• scale (True vs False)：scale=False略好
              <br/>• n_components：4个主成分最优，过多会过拟合
            </p>
          </div>
          <div className="flex items-start">
            <span className="text-2xl mr-3">4️⃣</span>
            <p><strong>稳定性</strong>：标准差 ±0.2775，说明模型在不同数据折上表现较稳定</p>
          </div>
        </div>
      </div>
    </div>
  );
}