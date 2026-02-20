import React from 'react';
import {
  Box,
  Typography,
  Container,
  Slide,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import { styled } from '@mui/material/styles';
import logo from '../images/simple_logo_legally_square.jpg';

const HeaderBox = styled(Box)(({ theme }) => ({
  background: '#000000',
  padding: theme.spacing(4, 0),
  color: '#FFFFFF',
  boxShadow: '0 4px 20px rgba(0,0,0,0.4)',
  position: 'relative',
  overflow: 'hidden',
  '&:before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: '4px',
    background: '#E60000',
  },
  '&:after': {
    content: '""',
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: '1px',
    background: 'rgba(255, 255, 255, 0.1)',
  },
}));

const AnimatedGradient = styled(Box)({
  position: 'absolute',
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  background:
    'linear-gradient(90deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0.1) 50%, rgba(255,255,255,0.03) 100%)',
  animation: 'shimmer 8s infinite linear',
  '@keyframes shimmer': {
    '0%': { transform: 'translateX(-100%)' },
    '100%': { transform: 'translateX(100%)' },
  },
});

function Header() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  return (
    <Slide
      in
      direction="down"
      timeout={700}
      easing="cubic-bezier(0.4, 0, 0.2, 1)"
    >
      <HeaderBox component="header">
        <AnimatedGradient />
        <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 1 }}>
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>
              <Box
                component="img"
                src={logo}
                alt="Logo"
                sx={{
                  height: isMobile ? 60 : 80,
                  borderRadius: '8px',
                  boxShadow: '0 4px 12px rgba(230,0,0,0.3)',
                  transition: 'transform 0.3s ease',
                  '&:hover': { transform: 'scale(1.05)' }
                }}
              />
              <Box>
                <Typography
                  variant={isMobile ? 'h5' : 'h3'}
                  component="h1"
                  sx={{
                    fontWeight: 800,
                    letterSpacing: '0.05em',
                    textTransform: 'uppercase',
                    color: '#FFFFFF',
                    mb: 0.5
                  }}
                >
                  Legally
                </Typography>
                <Box sx={{ width: '40px', height: '4px', background: '#E60000' }} />
              </Box>
            </Box>
            <Typography
              variant={isMobile ? 'subtitle2' : 'subtitle1'}
              sx={{
                maxWidth: '680px',
                lineHeight: 1.6,
                opacity: 0.9,
                letterSpacing: '0.02em',
                textShadow: '0 1px 2px rgba(0, 0, 0, 0.1)',
              }}
            >
              Профессиональная проверка юридических документов на соответствие
              законодательству Республики Казахстан с использованием
              искусственного интеллекта
            </Typography>
          </Box>
        </Container>
      </HeaderBox>
    </Slide>
  );
}

export default Header;
