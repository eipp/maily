'use client';

import { useEffect, useRef } from 'react';
import { useTheme } from 'next-themes';
import { throttle } from 'lodash';

type ParticleBackgroundProps = {
  color?: string;
  density?: number;
  speed?: number;
  interactive?: boolean;
  className?: string;
};

export default function ParticleBackground({
  color = '#3b82f6',
  density = 50,
  speed = 0.5,
  interactive = true,
  className = '',
}: ParticleBackgroundProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { resolvedTheme } = useTheme();
  const isDarkMode = resolvedTheme === 'dark';
  
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    // For devices with higher pixel ratios
    const dpr = window.devicePixelRatio || 1;
    
    // Set canvas to correct size accounting for retina displays
    const setCanvasDimensions = () => {
      canvas.width = window.innerWidth * dpr;
      canvas.height = window.innerHeight * dpr;
      canvas.style.width = `${window.innerWidth}px`;
      canvas.style.height = `${window.innerHeight}px`;
      ctx.scale(dpr, dpr);
    };
    
    setCanvasDimensions();
    
    // Handle window resize
    const handleResize = throttle(() => {
      setCanvasDimensions();
      initParticles();
    }, 200);
    
    window.addEventListener('resize', handleResize);
    
    // Mouse tracking for interactive mode
    let mouseX = -1000;
    let mouseY = -1000;
    
    const handleMouseMove = throttle((e: MouseEvent) => {
      mouseX = e.clientX;
      mouseY = e.clientY;
    }, 50);
    
    if (interactive) {
      window.addEventListener('mousemove', handleMouseMove);
    }
    
    // Particle system
    const particleCount = Math.floor((window.innerWidth * window.innerHeight) / (14000 / density));
    const particles: Particle[] = [];
    
    type Particle = {
      x: number;
      y: number;
      size: number;
      speedX: number;
      speedY: number;
      opacity: number;
    };
    
    // Initialize particles
    const initParticles = () => {
      particles.length = 0;
      for (let i = 0; i < particleCount; i++) {
        particles.push({
          x: Math.random() * window.innerWidth,
          y: Math.random() * window.innerHeight,
          size: Math.random() * 2 + 0.5,
          speedX: (Math.random() - 0.5) * speed,
          speedY: (Math.random() - 0.5) * speed,
          opacity: Math.random() * 0.5 + 0.1
        });
      }
    };
    
    initParticles();
    
    // Update and render particles
    const render = () => {
      // Clear canvas
      ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);
      
      // Update and draw particles
      particles.forEach((p, index) => {
        // Move particles
        p.x += p.speedX;
        p.y += p.speedY;
        
        // Boundary check with wrapping
        if (p.x > window.innerWidth) p.x = 0;
        else if (p.x < 0) p.x = window.innerWidth;
        
        if (p.y > window.innerHeight) p.y = 0;
        else if (p.y < 0) p.y = window.innerHeight;
        
        // Interactive effect - particles gravitate toward cursor
        if (interactive) {
          const dx = mouseX - p.x;
          const dy = mouseY - p.y;
          const distance = Math.sqrt(dx * dx + dy * dy);
          
          if (distance < 120) {
            const angle = Math.atan2(dy, dx);
            const force = (120 - distance) / 120 * 0.05;
            
            p.speedX += Math.cos(angle) * force;
            p.speedY += Math.sin(angle) * force;
          }
          
          // Add some friction to prevent extreme velocities
          p.speedX *= 0.98;
          p.speedY *= 0.98;
        }
        
        // Draw particle
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = color ? `${color}${Math.floor(p.opacity * 255).toString(16).padStart(2, '0')}` : 
                      isDarkMode ? `rgba(255, 255, 255, ${p.opacity})` : `rgba(59, 130, 246, ${p.opacity})`;
        ctx.fill();
        
        // Connect particles that are close to each other
        for (let j = index + 1; j < particles.length; j++) {
          const p2 = particles[j];
          const dx = p.x - p2.x;
          const dy = p.y - p2.y;
          const distance = Math.sqrt(dx * dx + dy * dy);
          
          if (distance < 100) {
            ctx.beginPath();
            ctx.strokeStyle = color ? `${color}${Math.floor((p.opacity * distance / 100) * 255).toString(16).padStart(2, '0')}` : 
                             isDarkMode ? `rgba(255, 255, 255, ${p.opacity * (1 - distance / 100)})` : 
                                         `rgba(59, 130, 246, ${p.opacity * (1 - distance / 100)})`;
            ctx.lineWidth = 0.5;
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();
          }
        }
      });
      
      requestAnimationFrame(render);
    };
    
    // Start animation
    const animationId = requestAnimationFrame(render);
    
    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      if (interactive) {
        window.removeEventListener('mousemove', handleMouseMove);
      }
      cancelAnimationFrame(animationId);
    };
  }, [color, density, speed, interactive, isDarkMode]);
  
  return (
    <canvas
      ref={canvasRef}
      className={`fixed inset-0 z-0 pointer-events-none ${className}`}
    />
  );
} 