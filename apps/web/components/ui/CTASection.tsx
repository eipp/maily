'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import { ArrowRight, Zap, Shield, LineChart } from 'lucide-react';
import ParticleBackground from './ParticleBackground';

interface CTASectionProps {
  title?: string;
  subtitle?: string;
  primaryCtaText?: string;
  primaryCtaHref?: string;
  secondaryCtaText?: string;
  secondaryCtaHref?: string;
  className?: string;
  showStatsBar?: boolean;
  statsBarItems?: {
    label: string;
    value: string;
    icon?: React.ReactNode;
  }[];
}

export default function CTASection({
  title = 'Ready to Transform Your Email Marketing?',
  subtitle = 'Join thousands of marketers who have already taken their campaigns to the next level with Maily.',
  primaryCtaText = 'Start Free Trial',
  primaryCtaHref = '/auth/register',
  secondaryCtaText = 'Learn More',
  secondaryCtaHref = '/features',
  className = '',
  showStatsBar = true,
  statsBarItems = [
    { 
      label: 'Deliverability Rate', 
      value: '99.8%', 
      icon: <Shield className="h-5 w-5 text-green-500" /> 
    },
    { 
      label: 'Average ROI', 
      value: '287%', 
      icon: <LineChart className="h-5 w-5 text-blue-500" /> 
    },
    { 
      label: 'Setup Time', 
      value: '5 minutes', 
      icon: <Zap className="h-5 w-5 text-amber-500" /> 
    },
  ],
}: CTASectionProps) {
  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 },
  };

  return (
    <section className={`relative overflow-hidden py-24 ${className}`}>
      {/* Background effects */}
      <div className="absolute inset-0 -z-10">
        <ParticleBackground 
          className="absolute inset-0"
          color="var(--color-primary)"
          density={0.3}
          speed={0.1}
          interactive={false}
        />
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-background/40 dark:via-background-dark/40 to-background dark:to-background-dark backdrop-blur-sm" />
      </div>
      
      <div className="container mx-auto px-4 md:px-6 relative z-10">
        <motion.div
          className="max-w-5xl mx-auto text-center"
          variants={containerVariants}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-100px" }}
        >
          <motion.h2 
            className="text-3xl sm:text-4xl md:text-5xl font-bold mb-6 gradient-text"
            variants={itemVariants}
          >
            {title}
          </motion.h2>
          
          <motion.p
            className="text-lg md:text-xl text-foreground/80 dark:text-foreground-dark/80 max-w-3xl mx-auto mb-10"
            variants={itemVariants}
          >
            {subtitle}
          </motion.p>
          
          <motion.div
            className="flex flex-col sm:flex-row gap-4 justify-center mb-12"
            variants={itemVariants}
          >
            <Link
              href={primaryCtaHref}
              className="inline-flex items-center justify-center px-8 py-4 rounded-xl bg-gradient-to-r from-primary to-primary-600 text-white font-medium shadow-lg shadow-primary/20 hover:shadow-xl hover:shadow-primary/30 hover:scale-105 transition-all duration-200 text-base md:text-lg"
            >
              {primaryCtaText}
              <ArrowRight className="ml-2 h-5 w-5" />
            </Link>
            
            <Link
              href={secondaryCtaHref}
              className="inline-flex items-center justify-center px-8 py-4 rounded-xl bg-background/60 dark:bg-background-dark/60 backdrop-blur-sm border border-border/40 dark:border-border-dark/40 font-medium hover:bg-background/80 dark:hover:bg-background-dark/80 transition-all duration-200 text-base md:text-lg"
            >
              {secondaryCtaText}
            </Link>
          </motion.div>
          
          {/* Stats bar */}
          {showStatsBar && (
            <motion.div
              className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto"
              variants={itemVariants}
            >
              {statsBarItems.map((item, index) => (
                <div
                  key={index}
                  className="group relative overflow-hidden backdrop-blur-sm rounded-xl bg-background/30 dark:bg-background-dark/30 border border-border/20 dark:border-border-dark/20 shadow-glass hover:shadow-lg hover:border-primary/20 dark:hover:border-primary-dark/20 p-6 transition-all duration-300"
                >
                  <div className="flex items-center gap-3">
                    {item.icon && <div>{item.icon}</div>}
                    <div>
                      <p className="text-3xl font-bold text-foreground dark:text-foreground-dark">
                        {item.value}
                      </p>
                      <p className="text-sm text-foreground/60 dark:text-foreground-dark/60">
                        {item.label}
                      </p>
                    </div>
                  </div>
                  
                  {/* Decorative element */}
                  <div className="absolute -bottom-12 -right-12 w-24 h-24 bg-gradient-to-br from-primary/10 dark:from-primary-dark/10 to-transparent rounded-full blur-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                </div>
              ))}
            </motion.div>
          )}
          
          {/* Trust badges */}
          <motion.div 
            className="mt-16 flex flex-col items-center"
            variants={itemVariants}
          >
            <p className="text-sm text-foreground/60 dark:text-foreground-dark/60 mb-4">
              Trusted by leading companies worldwide
            </p>
            <div className="flex flex-wrap justify-center gap-x-8 gap-y-4 opacity-60 dark:opacity-40">
              {Array.from({ length: 5 }).map((_, index) => (
                <div key={index} className="h-8 w-24 bg-foreground/20 dark:bg-foreground-dark/20 rounded-md animate-pulse" />
              ))}
            </div>
          </motion.div>
          
          {/* Bottom decorative line */}
          <motion.div
            className="h-1 w-24 bg-gradient-to-r from-primary/40 to-primary-600/40 rounded-full mx-auto mt-16"
            variants={itemVariants}
          />
        </motion.div>
      </div>
    </section>
  );
} 