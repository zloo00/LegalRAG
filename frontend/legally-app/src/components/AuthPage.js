//AuthPage.js

import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  Box,
  Link,
  Divider,
  Fade,
  Alert,
  IconButton,
  InputAdornment,
  CircularProgress,
} from '@mui/material';
import {
  Lock,
  Person,
  Email,
  Visibility,
  VisibilityOff,
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import logo from '../images/hard_logo_legally.jpg';

const AuthPaper = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(4),
  borderRadius: theme.shape.borderRadius * 2,
  boxShadow: theme.shadows[4],
  maxWidth: 500,
  margin: '0 auto',
  position: 'relative',
  overflow: 'hidden',
  '&:before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 4,
    background: '#E60000',
  },
}));

function AuthPage({ type, onSuccess }) {
  const navigate = useNavigate();
  const [credentials, setCredentials] = React.useState({
    email: '',
    password: '',
    showPassword: false,
  });
  const [error, setError] = React.useState('');
  const [isLoading, setIsLoading] = React.useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const endpoint = type === 'login' ? '/api/login' : '/api/register';
      const response = await fetch(`http://localhost:8080${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: credentials.email,
          password: credentials.password,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Ошибка аутентификации');
      }

      const data = await response.json();

      // Сохраняем accessToken в localStorage
      if (data.accessToken) {
        localStorage.setItem('token', data.accessToken);
      } else {
        throw new Error('Токен авторизации отсутствует в ответе');
      }

      onSuccess?.();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Fade in timeout={600}>
      <Container maxWidth="sm" sx={{ py: 8 }}>
        <AuthPaper elevation={3}>
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mb: 4 }}>
            <Box
              component="img"
              src={logo}
              alt="Legally Logo"
              sx={{
                width: 120,
                height: 120,
                mb: 2,
                filter: 'drop-shadow(0 4px 8px rgba(0,0,0,0.1))',
                animation: 'fadeInScale 0.8s ease-out',
                '@keyframes fadeInScale': {
                  '0%': { opacity: 0, transform: 'scale(0.8)' },
                  '100%': { opacity: 1, transform: 'scale(1)' }
                }
              }}
            />
            <Typography variant="h4" align="center" sx={{ fontWeight: 700, color: '#000000' }}>
              {type === 'login' ? 'Вход в систему' : 'Регистрация'}
            </Typography>
            <Box sx={{ width: 40, height: 4, background: '#E60000', mt: 1 }} />
          </Box>

          {error && (
            <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
              {error}
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit}>
            <TextField
              fullWidth
              label="Email"
              type="email"
              margin="normal"
              value={credentials.email}
              onChange={(e) =>
                setCredentials({ ...credentials, email: e.target.value })
              }
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Email />
                  </InputAdornment>
                ),
              }}
            />

            <TextField
              fullWidth
              label="Пароль"
              type={credentials.showPassword ? 'text' : 'password'}
              margin="normal"
              value={credentials.password}
              onChange={(e) =>
                setCredentials({ ...credentials, password: e.target.value })
              }
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Lock />
                  </InputAdornment>
                ),
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={() =>
                        setCredentials({
                          ...credentials,
                          showPassword: !credentials.showPassword,
                        })
                      }
                    >
                      {credentials.showPassword ? (
                        <VisibilityOff />
                      ) : (
                        <Visibility />
                      )}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />

            <Button
              fullWidth
              variant="contained"
              size="large"
              type="submit"
              disabled={isLoading}
              startIcon={
                isLoading ? <CircularProgress size={20} color="inherit" /> : <Person />
              }
              sx={{
                mt: 3,
                bgcolor: '#E60000',
                '&:hover': { bgcolor: '#CC0000', transform: 'translateY(-2px)' },
                transition: 'all 0.3s ease'
              }}
            >
              {type === 'login' ? 'Войти' : 'Зарегистрироваться'}
            </Button>

            <Divider sx={{ my: 3 }} />

            <Typography align="center">
              {type === 'login' ? (
                <>
                  Нет аккаунта?{' '}
                  <Link
                    component="button"
                    onClick={() => navigate('/register')}
                  >
                    Зарегистрируйтесь
                  </Link>
                </>
              ) : (
                <>
                  Уже есть аккаунт?{' '}
                  <Link component="button" onClick={() => navigate('/login')}>
                    Войдите
                  </Link>
                </>
              )}
            </Typography>
          </Box>
        </AuthPaper>
      </Container>
    </Fade>
  );
}

export default AuthPage;
