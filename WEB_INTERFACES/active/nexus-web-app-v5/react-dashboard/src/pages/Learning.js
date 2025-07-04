import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

export default function Learning() {
  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ color: '#00ff00', mb: 3 }}>
        Learning Metrics
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography>Learning metrics dashboard coming soon...</Typography>
      </Paper>
    </Box>
  );
}