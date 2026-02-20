import React from 'react';
import {
    Box,
    List,
    ListItem,
    ListItemButton,
    ListItemIcon,
    ListItemText,
    Typography,
    Button,
    IconButton,
    Divider,
    Drawer,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import ChatBubbleOutlineIcon from '@mui/icons-material/ChatBubbleOutline';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import { styled } from '@mui/material/styles';

const SidebarContainer = styled(Box)(({ theme }) => ({
    width: '280px',
    height: '100%',
    backgroundColor: '#1e293b',
    color: 'white',
    display: 'flex',
    flexDirection: 'column',
    borderRight: '1px solid #334155',
}));

const NewChatButton = styled(Button)(({ theme }) => ({
    margin: '20px',
    padding: '12px',
    borderRadius: '12px',
    border: '1px solid #475569',
    color: 'white',
    textTransform: 'none',
    justifyContent: 'flex-start',
    '&:hover': {
        backgroundColor: '#334155',
        borderColor: '#64748b',
    },
}));

const SessionListItem = styled(ListItem)(({ theme, active }) => ({
    padding: '4px 12px',
    '&:hover .delete-btn': {
        opacity: 1,
    },
}));

const SessionButton = styled(ListItemButton)(({ theme, active }) => ({
    borderRadius: '8px',
    backgroundColor: active ? '#334155' : 'transparent',
    color: active ? 'white' : '#94a3b8',
    '&:hover': {
        backgroundColor: '#334155',
        color: 'white',
    },
}));

const Sidebar = ({ sessions, activeSessionId, onSelectSession, onNewChat, onDeleteSession }) => {
    return (
        <SidebarContainer>
            <NewChatButton
                fullWidth
                startIcon={<AddIcon />}
                onClick={onNewChat}
            >
                Новый чат
            </NewChatButton>

            <Typography
                variant="caption"
                sx={{ px: 3, py: 1, color: '#64748b', fontWeight: 'bold', textTransform: 'uppercase' }}
            >
                История чатов
            </Typography>

            <List sx={{ flex: 1, overflowY: 'auto', px: 1 }}>
                {sessions.map((session) => (
                    <SessionListItem
                        key={session.id}
                        disablePadding
                        secondaryAction={
                            <IconButton
                                edge="end"
                                className="delete-btn"
                                sx={{ opacity: 0, color: '#ef4444', p: 0.5, transition: 'opacity 0.2s' }}
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onDeleteSession(session.id);
                                }}
                            >
                                <DeleteOutlineIcon fontSize="small" />
                            </IconButton>
                        }
                    >
                        <SessionButton
                            active={activeSessionId === session.id}
                            onClick={() => onSelectSession(session.id)}
                        >
                            <ListItemIcon sx={{ minWidth: 40, color: 'inherit' }}>
                                <ChatBubbleOutlineIcon fontSize="small" />
                            </ListItemIcon>
                            <ListItemText
                                primary={session.title}
                                primaryTypographyProps={{
                                    variant: 'body2',
                                    noWrap: true,
                                    sx: { fontSize: '0.875rem' }
                                }}
                            />
                        </SessionButton>
                    </SessionListItem>
                ))}
            </List>

            <Divider sx={{ borderColor: '#334155' }} />
            <Box sx={{ p: 2 }}>
                <Typography variant="caption" sx={{ color: '#64748b' }}>
                    Legally AI v1.0
                </Typography>
            </Box>
        </SidebarContainer>
    );
};

export default Sidebar;
