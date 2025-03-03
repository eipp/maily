import React, { useState } from 'react';
import {
  AppBar,
  Box,
  CssBaseline,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  Menu as MenuIcon,
  ChevronLeft as ChevronLeftIcon,
  Dashboard,
  Email,
  Campaign,
  Analytics,
  Settings,
  ShowChart,
  Insights,
  Timeline,
  BarChart,
} from '@mui/icons-material';
import Link from 'next/link';
import { useRouter } from 'next/router';

const drawerWidth = 240;

interface DashboardLayoutProps {
  children: React.ReactNode;
}

const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [mobileOpen, setMobileOpen] = useState(false);
  const router = useRouter();

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const isActive = (path: string) => {
    return router.pathname === path || router.pathname.startsWith(`${path}/`);
  };

  const menuItems = [
    { text: 'Dashboard', icon: <Dashboard />, path: '/dashboard' },
    { text: 'Emails', icon: <Email />, path: '/emails' },
    { text: 'Campaigns', icon: <Campaign />, path: '/campaigns' },
    {
      text: 'Analytics',
      icon: <Analytics />,
      path: '/analytics',
      subItems: [
        { text: 'Overview', icon: <BarChart />, path: '/analytics' },
        { text: 'Performance', icon: <Timeline />, path: '/analytics/performance' },
        { text: 'Predictive', icon: <ShowChart />, path: '/analytics/predictive' },
        { text: 'Insights', icon: <Insights />, path: '/analytics/insights' },
      ],
    },
    { text: 'Settings', icon: <Settings />, path: '/settings' },
  ];

  const drawer = (
    <div>
      <Toolbar>
        <Typography variant="h6" noWrap component="div">
          Maily
        </Typography>
        {isMobile && (
          <IconButton onClick={handleDrawerToggle} sx={{ ml: 'auto' }}>
            <ChevronLeftIcon />
          </IconButton>
        )}
      </Toolbar>
      <Divider />
      <List>
        {menuItems.map((item) => (
          <React.Fragment key={item.text}>
            <Link href={item.path} passHref legacyBehavior>
              <ListItem
                disablePadding
                component="a"
                sx={{
                  bgcolor: isActive(item.path) && !item.subItems ? 'rgba(0, 0, 0, 0.08)' : 'transparent',
                }}
              >
                <ListItemButton>
                  <ListItemIcon>{item.icon}</ListItemIcon>
                  <ListItemText primary={item.text} />
                </ListItemButton>
              </ListItem>
            </Link>
            {item.subItems && (
              <List disablePadding>
                {item.subItems.map((subItem) => (
                  <Link key={subItem.text} href={subItem.path} passHref legacyBehavior>
                    <ListItem
                      disablePadding
                      component="a"
                      sx={{
                        pl: 4,
                        bgcolor: isActive(subItem.path) ? 'rgba(0, 0, 0, 0.08)' : 'transparent',
                      }}
                    >
                      <ListItemButton>
                        <ListItemIcon>{subItem.icon}</ListItemIcon>
                        <ListItemText primary={subItem.text} />
                      </ListItemButton>
                    </ListItem>
                  </Link>
                ))}
              </List>
            )}
          </React.Fragment>
        ))}
      </List>
    </div>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div">
            Maily
          </Typography>
        </Toolbar>
      </AppBar>
      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
        aria-label="mailbox folders"
      >
        {/* Mobile drawer */}
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // Better open performance on mobile.
          }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
        >
          {drawer}
        </Drawer>
        {/* Desktop drawer */}
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          mt: '64px', // AppBar height
        }}
      >
        {children}
      </Box>
    </Box>
  );
};

export default DashboardLayout;
