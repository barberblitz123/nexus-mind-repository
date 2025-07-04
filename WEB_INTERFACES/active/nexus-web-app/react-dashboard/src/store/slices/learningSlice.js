import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

export const fetchLearningMetrics = createAsyncThunk(
  'learning/fetchMetrics',
  async () => {
    const response = await axios.get('/api/v2/learning/metrics');
    return response.data;
  }
);

export const fetchLearningHistory = createAsyncThunk(
  'learning/fetchHistory',
  async (hours = 24) => {
    const response = await axios.get(`/api/v2/learning/history?hours=${hours}`);
    return response.data;
  }
);

const learningSlice = createSlice({
  name: 'learning',
  initialState: {
    metrics: {
      total_goals: 0,
      completed_goals: 0,
      accuracy_rate: 0.95,
      learning_rate: 0.02,
      adaptations: 0,
      knowledge_nodes: 0,
      active_patterns: 0,
    },
    history: [],
    loading: false,
    error: null,
  },
  reducers: {
    updateMetrics: (state, action) => {
      state.metrics = { ...state.metrics, ...action.payload };
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchLearningMetrics.fulfilled, (state, action) => {
        state.metrics = action.payload;
      })
      .addCase(fetchLearningHistory.fulfilled, (state, action) => {
        state.history = action.payload;
      });
  },
});

export const { updateMetrics } = learningSlice.actions;
export default learningSlice.reducer;