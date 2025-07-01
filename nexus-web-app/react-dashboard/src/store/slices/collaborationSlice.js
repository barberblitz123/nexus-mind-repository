import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

export const initiateCollaboration = createAsyncThunk(
  'collaboration/initiate',
  async (collaborationData) => {
    const response = await axios.post('/api/v2/collaborate', collaborationData);
    return response.data;
  }
);

const collaborationSlice = createSlice({
  name: 'collaboration',
  initialState: {
    activeCollaborations: [],
    agentStatus: {},
    connections: [],
    loading: false,
    error: null,
  },
  reducers: {
    updateAgentStatus: (state, action) => {
      const { agentId, status } = action.payload;
      state.agentStatus[agentId] = status;
    },
    addConnection: (state, action) => {
      state.connections.push(action.payload);
    },
    removeConnection: (state, action) => {
      state.connections = state.connections.filter(c => c.id !== action.payload);
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(initiateCollaboration.pending, (state) => {
        state.loading = true;
      })
      .addCase(initiateCollaboration.fulfilled, (state, action) => {
        state.loading = false;
        state.activeCollaborations.push(action.payload);
      })
      .addCase(initiateCollaboration.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      });
  },
});

export const { updateAgentStatus, addConnection, removeConnection } = collaborationSlice.actions;
export default collaborationSlice.reducer;