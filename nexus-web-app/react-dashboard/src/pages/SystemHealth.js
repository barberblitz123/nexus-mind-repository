import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

export default function SystemHealth() {
  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ color: '#00ff00', mb: 3 }}>
        System Health Monitor
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography>System health monitoring coming soon...</Typography>
      </Paper>
    </Box>
  );
}