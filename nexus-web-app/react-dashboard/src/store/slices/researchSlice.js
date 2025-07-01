import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

export const conductResearch = createAsyncThunk(
  'research/conduct',
  async (researchData) => {
    const response = await axios.post('/api/v2/research', researchData);
    return response.data;
  }
);

export const fetchResearchHistory = createAsyncThunk(
  'research/fetchHistory',
  async (limit = 20) => {
    const response = await axios.get(`/api/v2/research?limit=${limit}`);
    return response.data;
  }
);

const researchSlice = createSlice({
  name: 'research',
  initialState: {
    items: [],
    activeResearch: null,
    loading: false,
    error: null,
  },
  reducers: {
    setActiveResearch: (state, action) => {
      state.activeResearch = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(conductResearch.pending, (state) => {
        state.loading = true;
      })
      .addCase(conductResearch.fulfilled, (state, action) => {
        state.loading = false;
        state.items.unshift(action.payload);
      })
      .addCase(conductResearch.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      })
      .addCase(fetchResearchHistory.fulfilled, (state, action) => {
        state.items = action.payload;
      });
  },
});

export const { setActiveResearch } = researchSlice.actions;
export default researchSlice.reducer;