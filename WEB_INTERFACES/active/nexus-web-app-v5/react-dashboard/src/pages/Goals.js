import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  Card,
  CardContent,
  Chip,
  LinearProgress,
  IconButton,
  Collapse,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
} from '@mui/material';
import {
  Add,
  ExpandMore,
  ExpandLess,
  CheckCircle,
  RadioButtonUnchecked,
  Schedule,
  Error,
} from '@mui/icons-material';
import { useSelector, useDispatch } from 'react-redux';
import { createGoal, fetchGoals, updateGoal } from '../store/slices/goalsSlice';

const GoalCard = ({ goal }) => {
  const [expanded, setExpanded] = useState(false);
  const dispatch = useDispatch();

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle sx={{ color: '#00ff00' }} />;
      case 'active':
      case 'in_progress':
        return <RadioButtonUnchecked sx={{ color: '#00ccff' }} />;
      case 'planning':
        return <Schedule sx={{ color: '#ff9800' }} />;
      case 'failed':
        return <Error sx={{ color: '#ff0000' }} />;
      default:
        return <RadioButtonUnchecked />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return '#00ff00';
      case 'active':
      case 'in_progress':
        return '#00ccff';
      case 'planning':
        return '#ff9800';
      case 'failed':
        return '#ff0000';
      default:
        return '#666666';
    }
  };

  return (
    <Card sx={{ mb: 2, background: 'rgba(255, 255, 255, 0.05)' }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start">
          <Box flex={1}>
            <Box display="flex" alignItems="center" mb={1}>
              {getStatusIcon(goal.status)}
              <Typography variant="h6" sx={{ ml: 1 }}>
                {goal.goal}
              </Typography>
            </Box>
            <Box display="flex" gap={1} mb={2}>
              <Chip
                label={goal.status}
                size="small"
                sx={{
                  backgroundColor: getStatusColor(goal.status),
                  color: '#000',
                }}
              />
              <Chip
                label={goal.priority}
                size="small"
                variant="outlined"
                sx={{ borderColor: '#00ff00' }}
              />
              <Typography variant="body2" color="text.secondary">
                Created: {new Date(goal.created_at).toLocaleString()}
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={goal.progress || 0}
              sx={{
                height: 8,
                borderRadius: 4,
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                '& .MuiLinearProgress-bar': {
                  backgroundColor: '#00ff00',
                },
              }}
            />
            <Typography variant="body2" sx={{ mt: 1 }}>
              Progress: {goal.progress || 0}%
            </Typography>
          </Box>
          <IconButton onClick={() => setExpanded(!expanded)}>
            {expanded ? <ExpandLess /> : <ExpandMore />}
          </IconButton>
        </Box>
        
        <Collapse in={expanded}>
          <Box mt={2}>
            {goal.sub_goals && goal.sub_goals.length > 0 && (
              <>
                <Typography variant="subtitle2" gutterBottom>
                  Sub-goals:
                </Typography>
                <List dense>
                  {goal.sub_goals.map((subGoal, index) => (
                    <ListItem key={index}>
                      <ListItemIcon>
                        <CheckCircle sx={{ fontSize: 16, color: '#00ff00' }} />
                      </ListItemIcon>
                      <ListItemText primary={subGoal} />
                    </ListItem>
                  ))}
                </List>
              </>
            )}
            
            {goal.expected_outcome && (
              <Box mt={2}>
                <Typography variant="subtitle2">Expected Outcome:</Typography>
                <Typography variant="body2" color="text.secondary">
                  {goal.expected_outcome}
                </Typography>
              </Box>
            )}
            
            {goal.learnings && Object.keys(goal.learnings).length > 0 && (
              <Box mt={2}>
                <Typography variant="subtitle2">Learnings:</Typography>
                <Typography variant="body2" color="text.secondary">
                  {JSON.stringify(goal.learnings, null, 2)}
                </Typography>
              </Box>
            )}
          </Box>
        </Collapse>
      </CardContent>
    </Card>
  );
};

export default function Goals() {
  const dispatch = useDispatch();
  const { items: goals, loading } = useSelector(state => state.goals);
  const [newGoal, setNewGoal] = useState({
    goal: '',
    priority: 'MEDIUM',
    expected_outcome: '',
  });
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    dispatch(fetchGoals());
  }, [dispatch]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (newGoal.goal.trim()) {
      await dispatch(createGoal(newGoal));
      setNewGoal({
        goal: '',
        priority: 'MEDIUM',
        expected_outcome: '',
      });
      // Refresh goals list
      dispatch(fetchGoals());
    }
  };

  const filteredGoals = goals.filter(goal => {
    if (filter === 'all') return true;
    return goal.status === filter;
  });

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ color: '#00ff00', mb: 3 }}>
        Goal Management
      </Typography>

      {/* Create New Goal */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Create New Goal
        </Typography>
        <form onSubmit={handleSubmit}>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Goal Description"
                value={newGoal.goal}
                onChange={(e) => setNewGoal({ ...newGoal, goal: e.target.value })}
                placeholder="Describe your goal in natural language..."
                multiline
                rows={2}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    '& fieldset': {
                      borderColor: 'rgba(0, 255, 0, 0.3)',
                    },
                    '&:hover fieldset': {
                      borderColor: 'rgba(0, 255, 0, 0.5)',
                    },
                    '&.Mui-focused fieldset': {
                      borderColor: '#00ff00',
                    },
                  },
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Priority</InputLabel>
                <Select
                  value={newGoal.priority}
                  onChange={(e) => setNewGoal({ ...newGoal, priority: e.target.value })}
                  label="Priority"
                >
                  <MenuItem value="LOW">Low</MenuItem>
                  <MenuItem value="MEDIUM">Medium</MenuItem>
                  <MenuItem value="HIGH">High</MenuItem>
                  <MenuItem value="CRITICAL">Critical</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Expected Outcome (Optional)"
                value={newGoal.expected_outcome}
                onChange={(e) => setNewGoal({ ...newGoal, expected_outcome: e.target.value })}
                placeholder="What do you expect to achieve?"
              />
            </Grid>
            <Grid item xs={12}>
              <Button
                type="submit"
                variant="contained"
                startIcon={<Add />}
                disabled={!newGoal.goal.trim() || loading}
                sx={{ mt: 1 }}
              >
                Submit Goal
              </Button>
            </Grid>
          </Grid>
        </form>
      </Paper>

      {/* Filter and Goals List */}
      <Paper sx={{ p: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h6">
            Goals ({filteredGoals.length})
          </Typography>
          <FormControl sx={{ minWidth: 150 }}>
            <InputLabel>Filter</InputLabel>
            <Select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              label="Filter"
              size="small"
            >
              <MenuItem value="all">All</MenuItem>
              <MenuItem value="planning">Planning</MenuItem>
              <MenuItem value="active">Active</MenuItem>
              <MenuItem value="completed">Completed</MenuItem>
              <MenuItem value="failed">Failed</MenuItem>
            </Select>
          </FormControl>
        </Box>

        <Box>
          {filteredGoals.length === 0 ? (
            <Typography variant="body1" color="text.secondary" textAlign="center" py={4}>
              No goals found
            </Typography>
          ) : (
            filteredGoals.map(goal => (
              <GoalCard key={goal.id} goal={goal} />
            ))
          )}
        </Box>
      </Paper>
    </Box>
  );
}