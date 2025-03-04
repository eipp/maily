'use client';

import { FC } from 'react';
import { motion } from 'framer-motion';

interface LoadingPulseProps {
  size?: 'sm' | 'md' | 'lg';
  color?: 'primary' | 'secondary' | 'white';
  text?: string;
  className?: string;
}

export const LoadingPulse: FC<LoadingPulseProps> = ({
  size = 'md',
  color = 'primary',
  text,
  className = ''
}) => {
  const sizeMap = {
    sm: 'w-6 h-6',
    md: 'w-12 h-12',
    lg: 'w-16 h-16',
  };

  const colorMap = {
    primary: 'text-primary-500',
    secondary: 'text-blue-500',
    white: 'text-white',
  };

  const pulseVariants = {
    initial: { scale: 0.8, opacity: 0.5 },
    animate: {
      scale: [0.8, 1, 0.8],
      opacity: [0.5, 1, 0.5],
      transition: {
        duration: 1.5,
        repeat: Infinity,
        ease: "easeInOut",
      }
    }
  };

  const circleVariants = {
    initial: { opacity: 0, y: 5 },
    animate: (i: number) => ({
      opacity: [0.5, 1, 0.5],
      y: [0, -10, 0],
      transition: {
        duration: 1,
        repeat: Infinity,
        delay: i * 0.2,
        ease: "easeInOut",
      }
    })
  };

  return (
    <div className={`flex flex-col items-center justify-center ${className}`}>
      <div className={`relative ${sizeMap[size]}`}>
        {/* Background pulse effect */}
        <motion.div
          className={`absolute inset-0 rounded-full bg-current ${colorMap[color]} opacity-20`}
          initial="initial"
          animate="animate"
          variants={pulseVariants}
        />
        
        {/* Animated circles */}
        <div className="absolute inset-0 flex items-center justify-center">
          {[0, 1, 2].map((i) => (
            <motion.div
              key={i}
              className={`mx-1 h-2 w-2 rounded-full ${colorMap[color]}`}
              variants={circleVariants}
              initial="initial"
              animate="animate"
              custom={i}
            />
          ))}
        </div>
      </div>
      
      {text && (
        <motion.p 
          className={`mt-4 text-sm ${colorMap[color]}`}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          {text}
        </motion.p>
      )}
    </div>
  );
};
