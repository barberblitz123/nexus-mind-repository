import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

export default function Research() {
  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ color: '#00ff00', mb: 3 }}>
        Research Lab
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography>Research interface coming soon...</Typography>
      </Paper>
    </Box>
  );
}