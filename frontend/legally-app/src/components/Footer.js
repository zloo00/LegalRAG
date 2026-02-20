// Footer.js

import React from 'react';
import {
  Box,
  Typography,
  Container,
  Fade,
  Link,
  Divider,
  useTheme,
} from '@mui/material';
import { styled } from '@mui/material/styles';

const FooterContainer = styled(Box)(({ theme }) => ({
  background: theme.palette.background.paper,
  padding: theme.spacing(6, 0),
  marginTop: theme.spacing(8),
  borderTop: `1px solid ${theme.palette.divider}`,
  position: 'relative',
  '&:before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: '3px',
    background: 'linear-gradient(90deg, #E60000, #000000)',
  },
}));

const FooterGrid = styled(Box)(({ theme }) => ({
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
  gap: theme.spacing(4),
  marginBottom: theme.spacing(4),
  [theme.breakpoints.down('sm')]: {
    gridTemplateColumns: '1fr',
    gap: theme.spacing(2),
  },
}));

function Footer() {
  const theme = useTheme();

  return (
    <Fade in timeout={800}>
      <FooterContainer component="footer">
        <Container maxWidth="lg">
          <FooterGrid>
            <Box>
              <Typography
                variant="h6"
                color="text.primary"
                gutterBottom
                sx={{ fontWeight: 600 }}
              >
                Legally
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Профессиональный анализ юридических документов с использованием
                AI
              </Typography>
            </Box>

            <Box>
              <Typography
                variant="subtitle1"
                color="text.primary"
                gutterBottom
                sx={{ fontWeight: 500 }}
              >
                Контакты
              </Typography>
              <Typography variant="body2" color="text.secondary">
                <Link
                  href="mailto:info@legally.kz"
                  color="inherit"
                  underline="hover"
                >
                  alua.zholdykan@narxoz.kz
                </Link>
              </Typography>
              <Typography variant="body2" color="text.secondary">
                <Link href="tel:+77771234567" color="inherit" underline="hover">
                  +7 (776) 021-64-89
                </Link>
              </Typography>
            </Box>

            <Box>
              <Typography
                variant="subtitle1"
                color="text.primary"
                gutterBottom
                sx={{ fontWeight: 500 }}
              >
                Юридическая информация
              </Typography>
              <Link
                href="#"
                variant="body2"
                color="text.secondary"
                display="block"
                underline="hover"
                mb={1}
              >
                Политика конфиденциальности
              </Link>
              <Link
                href="#"
                variant="body2"
                color="text.secondary"
                display="block"
                underline="hover"
              >
                Условия использования
              </Link>
            </Box>
          </FooterGrid>

          <Divider sx={{ my: 2, borderColor: theme.palette.divider }} />

          <Box
            sx={{
              display: 'flex',
              flexDirection: { xs: 'column', sm: 'row' },
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <Typography variant="body2" color="text.secondary">
              © {new Date().getFullYear()} Legally. Все права защищены.
            </Typography>
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ mt: { xs: 1, sm: 0 } }}
            >
              Информация не является юридической консультацией. Для важных
              решений обратитесь к юристу.
            </Typography>
          </Box>
        </Container>
      </FooterContainer>
    </Fade>
  );
}

export default Footer;
