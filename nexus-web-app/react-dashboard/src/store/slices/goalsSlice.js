import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

// Async thunks
export const createGoal = createAsyncThunk(
  'goals/create',
  async (goalData) => {
    const response = await axios.post('/api/v2/goals', goalData);
    return response.data;
  }
);

export const fetchGoals = createAsyncThunk(
  'goals/fetchAll',
  async () => {
    const response = await axios.get('/api/v2/goals');
    return response.data;
  }
);

export const updateGoal = createAsyncThunk(
  'goals/update',
  async ({ goalId, updateData }) => {
    const response = await axios.put(`/api/v2/goals/${goalId}`, updateData);
    return response.data;
  }
);

const goalsSlice = createSlice({
  name: 'goals',
  initialState: {
    items: [],
    activeGoal: null,
    loading: false,
    error: null,
  },
  reducers: {
    setActiveGoal: (state, action) => {
      state.activeGoal = action.payload;
    },
    updateGoalProgress: (state, action) => {
      const { goalId, progress } = action.payload;
      const goal = state.items.find(g => g.id === goalId);
      if (goal) {
        goal.progress = progress;
      }
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(createGoal.pending, (state) => {
        state.loading = true;
      })
      .addCase(createGoal.fulfilled, (state, action) => {
        state.loading = false;
        state.items.unshift({
          id: action.payload.goal_id,
          status: 'created',
          progress: 0,
          ...action.meta.arg,
        });
      })
      .addCase(createGoal.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      })
      .addCase(fetchGoals.fulfilled, (state, action) => {
        state.items = action.payload;
      });
  },
});

export const { setActiveGoal, updateGoalProgress } = goalsSlice.actions;
export default goalsSlice.reducer;