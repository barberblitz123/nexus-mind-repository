import React, { useEffect, useState } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  LinearProgress,
  Chip,
  Button,
} from '@mui/material';
import {
  TrendingUp,
  Memory,
  Speed,
  CheckCircle,
  RadioButtonChecked,
} from '@mui/icons-material';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { useSelector, useDispatch } from 'react-redux';
import { fetchGoals } from '../store/slices/goalsSlice';
import io from 'socket.io-client';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const MetricCard = ({ title, value, icon, color = '#00ff00', trend }) => (
  <Card sx={{ height: '100%', background: 'rgba(255, 255, 255, 0.05)' }}>
    <CardContent>
      <Box display="flex" justifyContent="space-between" alignItems="center">
        <Box>
          <Typography variant="body2" color="text.secondary">
            {title}
          </Typography>
          <Typography variant="h4" sx={{ color, fontWeight: 'bold', mt: 1 }}>
            {value}
          </Typography>
          {trend && (
            <Box display="flex" alignItems="center" mt={1}>
              <TrendingUp sx={{ fontSize: 16, mr: 0.5, color: trend > 0 ? '#00ff00' : '#ff0000' }} />
              <Typography variant="body2" sx={{ color: trend > 0 ? '#00ff00' : '#ff0000' }}>
                {trend > 0 ? '+' : ''}{trend}%
              </Typography>
            </Box>
          )}
        </Box>
        <Box sx={{ color, opacity: 0.3 }}>
          {icon}
        </Box>
      </Box>
    </CardContent>
  </Card>
);

export default function Dashboard() {
  const dispatch = useDispatch();
  const goals = useSelector(state => state.goals.items);
  const [systemMetrics, setSystemMetrics] = useState({
    activeAgents: 7,
    memoryUtilization: 84,
    processingSpeed: 1.2,
    accuracyRate: 95,
  });

  useEffect(() => {
    dispatch(fetchGoals());

    // Connect to WebSocket for real-time updates
    const socket = io('/general');
    
    socket.on('health_update', (data) => {
      setSystemMetrics(prev => ({
        ...prev,
        activeAgents: data.active_agents || prev.activeAgents,
        memoryUtilization: data.memory_utilization || prev.memoryUtilization,
        processingSpeed: data.processing_speed || prev.processingSpeed,
      }));
    });

    return () => socket.disconnect();
  }, [dispatch]);

  // Chart data
  const chartData = {
    labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '24:00'],
    datasets: [
      {
        label: 'Learning Progress',
        data: [65, 68, 72, 78, 82, 88, 95],
        fill: true,
        backgroundColor: 'rgba(0, 255, 0, 0.1)',
        borderColor: '#00ff00',
        tension: 0.4,
      },
      {
        label: 'System Load',
        data: [30, 45, 38, 52, 48, 55, 40],
        fill: true,
        backgroundColor: 'rgba(0, 204, 255, 0.1)',
        borderColor: '#00ccff',
        tension: 0.4,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          color: '#fff',
        },
      },
    },
    scales: {
      x: {
        grid: {
          color: 'rgba(255, 255, 255, 0.1)',
        },
        ticks: {
          color: '#fff',
        },
      },
      y: {
        grid: {
          color: 'rgba(255, 255, 255, 0.1)',
        },
        ticks: {
          color: '#fff',
        },
      },
    },
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ color: '#00ff00', mb: 3 }}>
        System Overview
      </Typography>

      <Grid container spacing={3}>
        {/* Metrics Cards */}
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Active Agents"
            value={systemMetrics.activeAgents}
            icon={<RadioButtonChecked sx={{ fontSize: 40 }} />}
            trend={12}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Memory Utilization"
            value={`${systemMetrics.memoryUtilization}%`}
            icon={<Memory sx={{ fontSize: 40 }} />}
            color="#00ccff"
            trend={-3}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Processing Speed"
            value={`${systemMetrics.processingSpeed}ms`}
            icon={<Speed sx={{ fontSize: 40 }} />}
            color="#ff9800"
            trend={8}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Accuracy Rate"
            value={`${systemMetrics.accuracyRate}%`}
            icon={<CheckCircle sx={{ fontSize: 40 }} />}
            color="#4caf50"
            trend={2}
          />
        </Grid>

        {/* Performance Chart */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3, height: 400 }}>
            <Typography variant="h6" gutterBottom>
              System Performance
            </Typography>
            <Box sx={{ height: 320 }}>
              <Line data={chartData} options={chartOptions} />
            </Box>
          </Paper>
        </Grid>

        {/* Active Goals */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, height: 400, overflow: 'auto' }}>
            <Typography variant="h6" gutterBottom>
              Active Goals
            </Typography>
            <Box>
              {goals.slice(0, 5).map((goal) => (
                <Box key={goal.id} sx={{ mb: 2 }}>
                  <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Typography variant="body2" noWrap sx={{ flex: 1 }}>
                      {goal.goal}
                    </Typography>
                    <Chip
                      label={goal.status}
                      size="small"
                      sx={{
                        ml: 1,
                        backgroundColor: goal.status === 'completed' ? '#00ff00' : '#ff9800',
                        color: '#000',
                      }}
                    />
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={goal.progress || 0}
                    sx={{
                      mt: 1,
                      backgroundColor: 'rgba(255, 255, 255, 0.1)',
                      '& .MuiLinearProgress-bar': {
                        backgroundColor: '#00ff00',
                      },
                    }}
                  />
                </Box>
              ))}
              {goals.length === 0 && (
                <Typography variant="body2" color="text.secondary">
                  No active goals
                </Typography>
              )}
            </Box>
          </Paper>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            <Grid container spacing={2}>
              <Grid item>
                <Button variant="contained" onClick={() => console.log('Run Analysis')}>
                  Run Full Analysis
                </Button>
              </Grid>
              <Grid item>
                <Button variant="contained" onClick={() => console.log('Optimize')}>
                  Optimize Performance
                </Button>
              </Grid>
              <Grid item>
                <Button variant="contained" onClick={() => console.log('Generate Report')}>
                  Generate Report
                </Button>
              </Grid>
              <Grid item>
                <Button variant="contained" onClick={() => console.log('Switch Context')}>
                  Switch Context
                </Button>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}