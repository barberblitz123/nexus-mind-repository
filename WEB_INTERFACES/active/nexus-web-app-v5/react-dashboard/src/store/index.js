import { configureStore } from '@reduxjs/toolkit';
import goalsReducer from './slices/goalsSlice';
import learningReducer from './slices/learningSlice';
import systemReducer from './slices/systemSlice';
import researchReducer from './slices/researchSlice';
import collaborationReducer from './slices/collaborationSlice';

export const store = configureStore({
  reducer: {
    goals: goalsReducer,
    learning: learningReducer,
    system: systemReducer,
    research: researchReducer,
    collaboration: collaborationReducer,
  },
});