import { createSlice } from '@reduxjs/toolkit';

const systemSlice = createSlice({
  name: 'system',
  initialState: {
    health: {
      activeAgents: 0,
      memoryUtilization: 0,
      processingSpeed: 0,
      accuracyRate: 0,
    },
    connected: false,
    notifications: [],
  },
  reducers: {
    updateHealth: (state, action) => {
      state.health = { ...state.health, ...action.payload };
    },
    setConnected: (state, action) => {
      state.connected = action.payload;
    },
    addNotification: (state, action) => {
      state.notifications.push({
        id: Date.now(),
        timestamp: new Date().toISOString(),
        ...action.payload,
      });
    },
    removeNotification: (state, action) => {
      state.notifications = state.notifications.filter(n => n.id !== action.payload);
    },
  },
});

export const { updateHealth, setConnected, addNotification, removeNotification } = systemSlice.actions;
export default systemSlice.reducer;