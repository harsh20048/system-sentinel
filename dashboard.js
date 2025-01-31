import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import {
  AlertCircle,
  Server,
  Cpu,
  MemoryStick,
  HardDrive,
  Network,
  ChevronRight,
} from 'lucide-react';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Loader2 } from 'lucide-react';

const SystemMonitor = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/current');

      if (!response.ok) {
        if (
          response.status === 401 ||
          (response.status === 500 && (await response.json()).suggest_admin)
        ) {
          throw new Error('Administrative privileges required');
        }
        throw new Error('Failed to fetch system data');
      }

      const result = await response.json();
      setData(result);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRetryWithAdmin = async () => {
    try {
      const response = await fetch('/retry_with_admin');
      if (response.ok) {
        fetchData();
      }
    } catch (err) {
      setError('Failed to obtain administrative access');
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <Card className="w-full max-w-4xl">
        <CardContent className="p-6 flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive" className="w-full max-w-4xl">
        <AlertDescription>
          {error}
          {error.includes('Administrative privileges') && (
            <Button onClick={handleRetryWithAdmin} className="mt-4" variant="secondary">
              Retry with Admin Privileges
            </Button>
          )}
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <Card className="w-full max-w-4xl">
      <CardHeader>
        <CardTitle>System Diagnostics</CardTitle>
      </CardHeader>
      <CardContent>
        {data && (
          <div className="space-y-4">
            <div>
              <h3 className="font-medium mb-2">System Info</h3>
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(data.diagnostics.system_info || {}).map(([key, value]) => (
                  <div key={key} className="text-sm">
                    <span className="font-medium">{key}: </span>
                    {String(value)}
                  </div>
                ))}
              </div>
            </div>

            {data.analysis && (
              <div>
                <h3 className="font-medium mb-2">Analysis</h3>
                <div className="text-sm">
                  <div>Status: {data.analysis.status}</div>
                  {data.analysis.warnings?.length > 0 && (
                    <div className="mt-2">
                      <div className="font-medium">Warnings:</div>
                      <ul className="list-disc pl-4">
                        {data.analysis.warnings.map((warning, idx) => (
                          <li key={idx}>{warning}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

const SystemMonitorDashboard = () => {
  const [systemData, setSystemData] = useState({
    cpu: { usage: 45, temperature: 62 },
    memory: { used: 65, total: 16 },
    disk: [
      { name: 'C:', usage: 75 },
      { name: 'D:', usage: 40 },
    ],
    network: { download: 85, upload: 45 },
  });

  const [alerts, setAlerts] = useState([
    {
      type: 'warning',
      message: 'High CPU Usage',
      timestamp: '2024-01-26 14:32',
    },
    {
      type: 'critical',
      message: 'Low Disk Space on C:',
      timestamp: '2024-01-26 14:15',
    },
  ]);

  const cpuData = [
    { name: '12am', usage: 30 },
    { name: '6am', usage: 45 },
    { name: '12pm', usage: 65 },
    { name: '6pm', usage: 55 },
  ];

  return (
    <div className="bg-gray-100 min-h-screen p-6">
      <div className="container mx-auto">
        <header className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-800">System Monitor Pro</h1>
          <div className="flex items-center space-x-4">
            <span className="text-green-600 font-semibold">Connected</span>
            <Server color="green" size={24} />
          </div>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="flex justify-between items-center mb-4">
              <div className="flex items-center space-x-2">
                <Cpu />
                <h2 className="text-xl font-semibold">CPU</h2>
              </div>
              <span
                className={`px-2 py-1 rounded ${
                  systemData.cpu.usage > 80
                    ? 'bg-red-100 text-red-600'
                    : 'bg-green-100 text-green-600'
                }`}
              >
                {systemData.cpu.usage}%
              </span>
            </div>
            <ResponsiveContainer width="100%" height={100}>
              <LineChart data={cpuData}>
                <Line type="monotone" dataKey="usage" stroke="#8884d8" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="flex justify-between items-center mb-4">
              <div className="flex items-center space-x-2">
                <MemoryStick />
                <h2 className="text-xl font-semibold">Memory</h2>
              </div>
              <span
                className={`px-2 py-1 rounded ${
                  systemData.memory.used > 80
                    ? 'bg-red-100 text-red-600'
                    : 'bg-green-100 text-green-600'
                }`}
              >
                {systemData.memory.used}%
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div
                  className="bg-blue-600 h-2.5 rounded-full"
                  style={{ width: `${systemData.memory.used}%` }}
                ></div>
              </div>
              <span>{systemData.memory.total} GB</span>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="flex justify-between items-center mb-4">
              <div className="flex items-center space-x-2">
                <AlertCircle color="orange" />
                <h2 className="text-xl font-semibold">Alerts</h2>
              </div>
              <span className="bg-red-100 text-red-600 px-2 py-1 rounded">
                {alerts.length}
              </span>
            </div>
            {alerts.slice(0, 3).map((alert, index) => (
              <div
                key={index}
                className={`flex justify-between items-center p-2 rounded mb-2 ${
                  alert.type === 'critical'
                    ? 'bg-red-50 border-l-4 border-red-500'
                    : 'bg-yellow-50 border-l-4 border-yellow-500'
                }`}
              >
                <div>
                  <p className="font-medium">{alert.message}</p>
                  <p className="text-xs text-gray-500">{alert.timestamp}</p>
                </div>
                <ChevronRight size={16} />
              </div>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="flex justify-between items-center mb-4">
              <div className="flex items-center space-x-2">
                <HardDrive />
                <h2 className="text-xl font-semibold">Disk Usage</h2>
              </div>
            </div>
            {systemData.disk.map((disk, index) => (
              <div key={index} className="mb-4">
                <div className="flex justify-between mb-2">
                  <span>{disk.name}</span>
                  <span>{disk.usage}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div
                    className={`h-2.5 rounded-full ${
                      disk.usage > 80 ? 'bg-red-500' : 'bg-green-500'
                    }`}
                    style={{ width: `${disk.usage}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>

          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="flex justify-between items-center mb-4">
              <div className="flex items-center space-x-2">
                <Network />
                <h2 className="text-xl font-semibold">Network</h2>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center">
                <div className="flex justify-center items-center space-x-2 mb-2">
                  <span>&#8595;</span>
                  <span className="font-semibold">{systemData.network.download} Mbps</span>
                </div>
                <p className="text-sm text-gray-500">Download Speed</p>
              </div>
              <div className="text-center">
                <div className="flex justify-center items-center space-x-2 mb-2">
                  <span>&#8593;</span>
                  <span className="font-semibold">{systemData.network.upload} Mbps</span>
                </div>
                <p className="text-sm text-gray-500">Upload Speed</p>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-6">
          <SystemMonitor />
        </div>
      </div>
    </div>
  );
};

export default SystemMonitorDashboard;
