'use client';

import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { ArrowRight, Sparkles, Zap, ArrowUpRight } from 'lucide-react';
import ParticleBackground from './ParticleBackground';
import AINetworkGraph from './AINetworkGraph';
import { analytics } from '../../utils/analytics';

interface HeroProps {
  title?: string;
  subtitle?: string;
  ctaText?: string;
  ctaHref?: string;
  secondaryCtaText?: string;
  secondaryCtaHref?: string;
  className?: string;
  showEmailCapture?: boolean;
  onSubmit?: (email: string) => Promise<void>;
}

export default function HeroSection({
  title = 'AI-Powered Email Marketing for the Future',
  subtitle = 'Leverage advanced AI technology to create, personalize, and optimize your email campaigns with unprecedented precision and effectiveness.',
  ctaText = 'Start Free Trial',
  ctaHref = '/auth/register',
  secondaryCtaText = 'View Demo',
  secondaryCtaHref = '#demo',
  className = '',
  showEmailCapture = true,
  onSubmit,
}: HeroProps) {
  const [email, setEmail] = useState('');
  const [isEmailValid, setIsEmailValid] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [highlightedNode, setHighlightedNode] = useState<string | null>(null);
  const [activeFeature, setActiveFeature] = useState(0);
  const formRef = useRef<HTMLFormElement>(null);
  
  const features = [
    {
      id: 'cognitive-canvas',
      title: 'Cognitive Canvas',
      description: 'Design emails that adapt to each recipient's preferences and behavior patterns',
      nodeId: 'node-1',
      icon: <Sparkles className="h-5 w-5" />
    },
    {
      id: 'ai-mesh',
      title: 'AI Mesh Network',
      description: 'Multiple specialized AI agents working in concert to optimize every aspect of your campaigns',
      nodeId: 'node-3',
      icon: <Zap className="h-5 w-5" />
    },
    {
      id: 'predictive-analytics',
      title: 'Predictive Analytics',
      description: 'Forecast campaign performance and identify opportunities before they happen',
      nodeId: 'node-4',
      icon: <ArrowUpRight className="h-5 w-5" />
    }
  ];
  
  // Auto-rotate featured items
  useEffect(() => {
    const interval = setInterval(() => {
      setActiveFeature((prev) => (prev + 1) % features.length);
      setHighlightedNode(features[(activeFeature + 1) % features.length].nodeId);
    }, 5000);
    
    return () => clearInterval(interval);
  }, [activeFeature]);
  
  // Update highlighted node when active feature changes
  useEffect(() => {
    setHighlightedNode(features[activeFeature].nodeId);
  }, [activeFeature]);
  
  // Validate email input
  const validateEmail = (email: string) => {
    const re = /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(String(email).toLowerCase());
  };
  
  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setEmail(value);
    setIsEmailValid(validateEmail(value));
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isEmailValid) return;
    
    setIsSubmitting(true);
    
    try {
      // Track form submission attempt
      analytics.trackEvent('email_submission_attempt', { source: 'hero_section' });
      
      if (onSubmit) {
        // Use the parent component's submit handler if provided
        await onSubmit(email);
      } else {
        // Default fallback behavior
        await new Promise(resolve => setTimeout(resolve, 1500));
        // Redirect to signup with email pre-filled
        window.location.href = `/auth/register?email=${encodeURIComponent(email)}`;
      }
      
      // Track successful submission
      analytics.trackEvent('email_submission_success', { source: 'hero_section' });
      
      // Reset form
      setEmail('');
      setIsEmailValid(false);
      
    } catch (error) {
      // Track submission error
      analytics.trackError(error as Error, { source: 'hero_section', action: 'email_submission' });
      console.error('Error submitting form:', error);
      // Optional: add error state handling here
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className={`relative overflow-hidden min-h-[90vh] flex items-center py-20 ${className}`}>
      {/* Particle background */}
      <ParticleBackground 
        className="absolute inset-0 -z-10"
        color="var(--color-primary)"
        density={0.5}
        speed={0.2}
        interactive={true}
      />
      
      <div className="container mx-auto px-4 md:px-6 relative z-10">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left column: Text content */}
          <div className="flex flex-col space-y-8">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
            >
              <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold tracking-tight mb-6 gradient-text">
                {title}
              </h1>
              <p className="text-lg md:text-xl text-foreground/80 dark:text-foreground-dark/80 max-w-xl leading-relaxed">
                {subtitle}
              </p>
            </motion.div>
            
            {/* Feature carousel */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.4 }}
              className="bg-background/30 dark:bg-background-dark/30 backdrop-blur-md rounded-xl p-6 border border-border/20 dark:border-border-dark/20 shadow-glass"
            >
              <div className="flex space-x-4 mb-4">
                {features.map((feature, index) => (
                  <button
                    key={feature.id}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                      activeFeature === index
                        ? 'bg-primary text-white shadow-lg'
                        : 'bg-background/50 dark:bg-background-dark/50 hover:bg-background/80 dark:hover:bg-background-dark/80'
                    }`}
                    onClick={() => {
                      setActiveFeature(index);
                      setHighlightedNode(feature.nodeId);
                    }}
                  >
                    <span className="flex items-center gap-2">
                      {feature.icon}
                      {feature.title}
                    </span>
                  </button>
                ))}
              </div>
              
              <div className="min-h-[100px] flex items-center">
                <div className="space-y-2">
                  <h3 className="text-xl font-bold flex items-center gap-2">
                    {features[activeFeature].icon}
                    {features[activeFeature].title}
                  </h3>
                  <p className="text-foreground/70 dark:text-foreground-dark/70">
                    {features[activeFeature].description}
                  </p>
                </div>
              </div>
            </motion.div>
            
            {/* CTA buttons */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.6 }}
              className="flex flex-col sm:flex-row gap-4"
            >
              <Link
                href={ctaHref}
                className="inline-flex items-center justify-center px-6 py-3 rounded-lg bg-gradient-to-r from-primary to-primary-600 text-white font-medium shadow-lg shadow-primary/20 hover:shadow-xl hover:shadow-primary/30 hover:scale-105 transition-all duration-200"
              >
                {ctaText}
                <ArrowRight className="ml-2 h-5 w-5" />
              </Link>
              
              <Link
                href={secondaryCtaHref}
                className="inline-flex items-center justify-center px-6 py-3 rounded-lg bg-background/40 dark:bg-background-dark/40 backdrop-blur-sm border border-border/40 dark:border-border-dark/40 font-medium hover:bg-background/60 dark:hover:bg-background-dark/60 transition-all duration-200"
              >
                {secondaryCtaText}
              </Link>
            </motion.div>
            
            {/* Email capture form */}
            {showEmailCapture && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.8 }}
                className="mt-8"
              >
                <form
                  ref={formRef}
                  onSubmit={handleSubmit}
                  className="flex max-w-md flex-col sm:flex-row gap-2"
                >
                  <div className="flex-1 relative">
                    <input
                      type="email"
                      value={email}
                      onChange={handleEmailChange}
                      placeholder="Enter your email"
                      className="w-full h-12 px-4 rounded-lg bg-background/60 dark:bg-background-dark/60 backdrop-blur-md border border-border/40 dark:border-border-dark/40 focus:ring-2 focus:ring-primary focus:border-transparent transition-all duration-200"
                      required
                    />
                    <div
                      className={`absolute bottom-0 left-0 h-[2px] bg-primary transition-all duration-300 ${
                        email ? 'w-full' : 'w-0'
                      }`}
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={!isEmailValid || isSubmitting}
                    className={`h-12 px-6 rounded-lg font-medium transition-all duration-200 ${
                      isEmailValid && !isSubmitting
                        ? 'bg-primary text-white hover:bg-primary-600'
                        : 'bg-gray-300 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed'
                    }`}
                  >
                    {isSubmitting ? (
                      <span className="flex items-center">
                        <svg
                          className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                          xmlns="http://www.w3.org/2000/svg"
                          fill="none"
                          viewBox="0 0 24 24"
                        >
                          <circle
                            className="opacity-25"
                            cx="12"
                            cy="12"
                            r="10"
                            stroke="currentColor"
                            strokeWidth="4"
                          />
                          <path
                            className="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                          />
                        </svg>
                        Processing
                      </span>
                    ) : (
                      'Get Started'
                    )}
                  </button>
                </form>
                <p className="mt-2 text-sm text-foreground/60 dark:text-foreground-dark/60">
                  No credit card required. Start your 14-day free trial today.
                </p>
              </motion.div>
            )}
          </div>
          
          {/* Right column: AI Network visualization */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.7, delay: 0.5 }}
            className="lg:block relative"
          >
            <div className="relative rounded-2xl overflow-hidden border border-border/20 dark:border-border-dark/20 shadow-2xl shadow-primary/20 aspect-square max-w-[600px] mx-auto">
              <AINetworkGraph 
                height={600} 
                className="w-full"
                interactive={true}
                highlightedNode={highlightedNode}
                onNodeHover={(nodeId) => nodeId && setHighlightedNode(nodeId)}
                density="medium"
              />
              
              {/* Decorative elements */}
              <div className="absolute top-4 right-4 px-3 py-1.5 rounded-full bg-background/40 dark:bg-background-dark/40 backdrop-blur-sm text-xs font-medium border border-border/20 dark:border-border-dark/20">
                AI Mesh Network
              </div>
              
              <div className="absolute bottom-4 left-4 flex space-x-2">
                {Array.from({ length: 3 }).map((_, i) => (
                  <div
                    key={i}
                    className={`w-2.5 h-2.5 rounded-full ${
                      i === activeFeature 
                        ? 'bg-primary' 
                        : 'bg-gray-400/30 dark:bg-gray-600/30'
                    }`}
                  />
                ))}
              </div>
            </div>
            
            {/* Stats cards */}
            <div className="absolute -bottom-6 -right-6 max-w-[180px] rounded-lg bg-background/80 dark:bg-background-dark/80 backdrop-blur-md p-4 border border-border/20 dark:border-border-dark/20 shadow-glass">
              <p className="text-sm text-foreground/70 dark:text-foreground-dark/70">Optimization</p>
              <p className="text-2xl font-bold">+287%</p>
              <div className="mt-1 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-green-400 to-emerald-500 w-[80%]" />
              </div>
            </div>
            
            <div className="absolute -top-4 -left-4 max-w-[180px] rounded-lg bg-background/80 dark:bg-background-dark/80 backdrop-blur-md p-4 border border-border/20 dark:border-border-dark/20 shadow-glass">
              <div className="flex justify-between items-center">
                <p className="text-sm text-foreground/70 dark:text-foreground-dark/70">AI Agents</p>
                <span className="flex h-2 w-2 relative">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
                </span>
              </div>
              <p className="text-2xl font-bold">Active</p>
              <div className="flex space-x-1 mt-1">
                {Array.from({ length: 6 }).map((_, i) => (
                  <div
                    key={i}
                    className="h-1.5 w-1.5 rounded-full bg-primary/80"
                    style={{
                      animationName: 'pulse',
                      animationDuration: '1.5s',
                      animationDelay: `${i * 0.2}s`,
                      animationIterationCount: 'infinite',
                    }}
                  />
                ))}
              </div>
            </div>
          </motion.div>
        </div>
      </div>
      
      {/* Decorative gradient */}
      <div className="absolute -z-10 top-1/4 left-0 right-0 h-[500px] bg-gradient-radial from-primary/20 to-transparent blur-3xl opacity-50" />
    </section>
  );
} 