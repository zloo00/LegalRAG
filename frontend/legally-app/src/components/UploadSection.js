import React, { useRef, useState } from 'react';
import {
  Container,
  Typography,
  Button,
  Alert,
  Fade,
  Stack,
  Box,
  CircularProgress,
  Paper,
  IconButton,
  useTheme,
  Tooltip,
} from '@mui/material';
import {
  UploadFile as UploadFileIcon,
  History as HistoryIcon,
  Description as DescriptionIcon,
  Close as CloseIcon,
  CloudUpload as CloudUploadIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import { formatFileSize } from '../utils/helpers';
import { useNavigate } from 'react-router-dom';

const FileUploadArea = styled(Box)(({ theme, $dragactive }) => ({
  padding: theme.spacing($dragactive ? 4 : 3),
  border: `2px dashed ${
    $dragactive ? theme.palette.primary.main : theme.palette.divider
  }`,
  borderRadius: theme.shape.borderRadius,
  backgroundColor: $dragactive
    ? theme.palette.action.hover
    : theme.palette.background.paper,
  transition: 'all 0.3s ease',
  textAlign: 'center',
  cursor: 'pointer',
  position: 'relative',
  '&:hover': {
    borderColor: theme.palette.primary.main,
    backgroundColor: theme.palette.action.hover,
  },
}));

const FileInfoBox = styled(Box)(({ theme }) => ({
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  gap: theme.spacing(1),
  marginTop: theme.spacing(2),
}));

function UploadSection({
  onFileUpload,
  fileInfo,
  error,
  onHistoryClick,
  isLoading = false,
  onClearError,
  onCancelUpload,
  onRemoveFile,
}) {
  const theme = useTheme();
  const fileInputRef = useRef(null);
  const [dragActive, setDragActive] = useState(false);
  const [fileError, setFileError] = useState(null);
  const navigate = useNavigate();

  const validateFile = (file) => {
    if (!file) return 'Файл не выбран';
    if (file.size > 10 * 1024 * 1024) {
      return `Файл слишком большой (${formatFileSize(
        file.size
      )}). Максимум 10MB`;
    }
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      return 'Поддерживаются только PDF файлы';
    }
    return null;
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    const validationError = validateFile(file);
    if (validationError) {
      setFileError(validationError);
      onFileUpload(null);
      fileInputRef.current.value = '';
      return;
    }
    setFileError(null);
    onFileUpload(file);
    setDragActive(false);
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(e.type === 'dragenter' || e.type === 'dragover');
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    const file = e.dataTransfer.files?.[0];
    const validationError = validateFile(file);
    if (validationError) {
      setFileError(validationError);
      onFileUpload(null);
      return;
    }
    setFileError(null);
    onFileUpload(file);
  };

  const handleSelectFileClick = () => {
    if (!fileInfo && !isLoading) {
      fileInputRef.current.click();
    }
  };

  return (
    <Fade in timeout={600}>
      <Container maxWidth="md" sx={{ mt: 6, mb: 4 }}>
        <Paper elevation={2} sx={{ p: 4, borderRadius: 2 }}>
          <Typography variant="h4" gutterBottom sx={{ fontWeight: 600 }}>
            Анализ юридических документов
          </Typography>

          {(error || fileError) && (
            <Alert
              severity="error"
              sx={{ mt: 2, mb: 3 }}
              action={
                <IconButton
                  size="small"
                  color="inherit"
                  onClick={() => {
                    onClearError();
                    setFileError(null);
                  }}
                >
                  <CloseIcon fontSize="small" />
                </IconButton>
              }
            >
              {error || fileError}
            </Alert>
          )}

          <FileUploadArea
            $dragactive={dragActive}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={handleSelectFileClick}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".pdf"
              hidden
            />

            {isLoading ? (
              <Box
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                }}
              >
                <CircularProgress
                  size={60}
                  thickness={4}
                  sx={{ mb: 2, color: theme.palette.primary.main }}
                />
                <Typography variant="h6">Идет анализ документа...</Typography>
                <Button
                  variant="outlined"
                  color="error"
                  onClick={(e) => {
                    e.stopPropagation();
                    onCancelUpload();
                  }}
                  sx={{ mt: 2 }}
                >
                  Отменить анализ
                </Button>
              </Box>
            ) : fileInfo ? (
              <>
                <DescriptionIcon
                  sx={{ fontSize: 60, color: 'primary.main', mb: 1 }}
                />
                <FileInfoBox>
                  <Typography variant="h6" gutterBottom>
                    {fileInfo.name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {formatFileSize(fileInfo.size)}
                  </Typography>
                  <Button
                    variant="outlined"
                    color="error"
                    startIcon={<CloseIcon />}
                    onClick={(e) => {
                      e.stopPropagation();
                      onRemoveFile();
                    }}
                    sx={{ mt: 2 }}
                  >
                    Удалить файл
                  </Button>
                </FileInfoBox>
              </>
            ) : (
              <>
                <CloudUploadIcon
                  sx={{ fontSize: 60, color: 'primary.main', mb: 2 }}
                />
                <Typography variant="h6" gutterBottom>
                  {dragActive
                    ? 'Отпустите файл для загрузки'
                    : 'Перетащите файл сюда или нажмите для выбора'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Поддерживаются только PDF файлы (максимум 10MB)
                </Typography>
              </>
            )}
          </FileUploadArea>

          <Stack
            direction="row"
            spacing={2}
            justifyContent="center"
            sx={{ mt: 4 }}
          >
            <Tooltip title="Выберите PDF файл для анализа">
              <Button
                variant={fileInfo ? 'outlined' : 'contained'}
                size="large"
                startIcon={<UploadFileIcon />}
                onClick={() => fileInputRef.current.click()}
                disabled={isLoading}
                sx={{
                  backgroundColor: fileInfo ? 'transparent' : undefined,
                }}
              >
                {fileInfo ? 'Заменить файл' : 'Выбрать файл'}
              </Button>
            </Tooltip>

            <Button
              variant="outlined"
              size="large"
              startIcon={<HistoryIcon />}
              onClick={() => navigate('/history')}
              disabled={isLoading}
            >
              История проверок
            </Button>
          </Stack>

          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              <InfoIcon
                fontSize="small"
                sx={{ mr: 0.5, verticalAlign: 'middle' }}
              />
              Система проверит ваш документ на соответствие законодательству РК
            </Typography>
          </Box>
        </Paper>
      </Container>
    </Fade>
  );
}

export default UploadSection;
