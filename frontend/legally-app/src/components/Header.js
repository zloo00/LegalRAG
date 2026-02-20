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

const HeaderBox = styled(Box)(({ theme }) => ({
  background: `linear-gradient(135deg, ${theme.palette.primary.dark} 0%, ${theme.palette.primary.main} 100%)`,
  padding: theme.spacing(8, 0),
  color: theme.palette.common.white,
  boxShadow: theme.shadows[4],
  position: 'relative',
  overflow: 'hidden',
  '&:before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: '4px',
    background: theme.palette.secondary.main,
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
            <Box>
              <Typography
                variant={isMobile ? 'h4' : 'h2'}
                component="h1"
                gutterBottom
                sx={{
                  fontWeight: 700,
                  letterSpacing: '0.03em',
                  textShadow: '0 2px 4px rgba(0, 0, 0, 0.2)',
                  '&:after': {
                    content: '""',
                    display: 'block',
                    width: '80px',
                    height: '4px',
                    background: theme.palette.secondary.light,
                    marginTop: theme.spacing(3),
                    [theme.breakpoints.down('sm')]: {
                      marginTop: theme.spacing(2),
                      width: '60px',
                      height: '3px',
                    },
                  },
                }}
              >
                Legally
              </Typography>
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
          </Box>
        </Container>
      </HeaderBox>
    </Slide>
  );
}

export default Header;
