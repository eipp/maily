'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { InfoIcon, AlertTriangleIcon, CheckCircleIcon } from 'lucide-react';

import { canvasPerformanceBenchmark } from '@/utils/canvasPerformanceBenchmark';
import { canvasPerformance } from '@/utils/canvasPerformance';

// Original Canvas component (imported for comparison)
import { Canvas } from '@/components/Canvas/Canvas';

// Optimized Canvas component
import { CollaborativeCanvas } from '@/components/Canvas/CollaborativeCanvas';

// Define benchmark scenarios
const SCENARIOS = [
  {
    name: 'Small Canvas (100 shapes)',
    shapeCount: 100,
    operations: [
      { type: 'render', count: 10 },
      { type: 'update', count: 50 },
      { type: 'collaboration', count: 20 },
      { type: 'interaction', count: 100 },
    ],
  },
  {
    name: 'Medium Canvas (500 shapes)',
    shapeCount: 500,
    operations: [
      { type: 'render', count: 10 },
      { type: 'update', count: 50 },
      { type: 'collaboration', count: 20 },
      { type: 'interaction', count: 100 },
    ],
  },
  {
    name: 'Large Canvas (2000 shapes)',
    shapeCount: 2000,
    operations: [
      { type: 'render', count: 5 },
      { type: 'update', count: 20 },
      { type: 'collaboration', count: 10 },
      { type: 'interaction', count: 50 },
    ],
  },
];

// Result card component
const ResultCard: React.FC<{
  title: string;
  value: number;
  unit: string;
  improvement?: number;
  higherIsBetter?: boolean;
}> = ({ title, value, unit, improvement, higherIsBetter = false }) => {
  // Format the improvement text and determine color
  let improvementText = '';
  let improvementColor = '';

  if (improvement !== undefined) {
    const sign = improvement > 0 ? '+' : '';
    improvementText = `${sign}${improvement.toFixed(2)}%`;

    if ((higherIsBetter && improvement > 0) || (!higherIsBetter && improvement < 0)) {
      improvementColor = 'text-green-500';
    } else if (improvement !== 0) {
      improvementColor = 'text-red-500';
    }
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">
          {value.toFixed(2)} {unit}
          {improvement !== undefined && (
            <span className={`ml-2 text-sm ${improvementColor}`}>
              {improvementText}
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

// Benchmark page component
export default function CanvasBenchmarkPage() {
  const [selectedScenario, setSelectedScenario] = useState(SCENARIOS[0].name);
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [originalResults, setOriginalResults] = useState<any>(null);
  const [optimizedResults, setOptimizedResults] = useState<any>(null);
  const [comparison, setComparison] = useState<any>(null);
  const [activeTab, setActiveTab] = useState('results');
  const [error, setError] = useState<string | null>(null);

  // Reset results when scenario changes
  useEffect(() => {
    setOriginalResults(null);
    setOptimizedResults(null);
    setComparison(null);
    setError(null);
  }, [selectedScenario]);

  // Run benchmark for original Canvas
  const runOriginalBenchmark = async () => {
    try {
      setIsRunning(true);
      setProgress(10);
      setError(null);

      // Find the selected scenario
      const scenario = SCENARIOS.find(s => s.name === selectedScenario);
      if (!scenario) {
        throw new Error('Scenario not found');
      }

      // Reset benchmark
      canvasPerformanceBenchmark.addScenario(scenario);

      setProgress(30);

      // Run benchmark
      const results = await canvasPerformanceBenchmark.runBenchmarks();

      setProgress(90);

      // Set results
      setOriginalResults(results[0]);

      setProgress(100);
    } catch (err) {
      console.error('Benchmark error:', err);
      setError(`Error running original benchmark: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setIsRunning(false);
    }
  };

  // Run benchmark for optimized Canvas
  const runOptimizedBenchmark = async () => {
    try {
      setIsRunning(true);
      setProgress(10);
      setError(null);

      // Find the selected scenario
      const scenario = SCENARIOS.find(s => s.name === selectedScenario);
      if (!scenario) {
        throw new Error('Scenario not found');
      }

      // Reset benchmark
      canvasPerformanceBenchmark.addScenario(scenario);

      setProgress(30);

      // Run benchmark
      const results = await canvasPerformanceBenchmark.runBenchmarks();

      setProgress(90);

      // Set results
      setOptimizedResults(results[0]);

      setProgress(100);

      // Generate comparison if both results are available
      if (originalResults) {
        const comparisonData = canvasPerformanceBenchmark.compareResults(
          originalResults,
          results[0]
        );
        setComparison(comparisonData);
      }
    } catch (err) {
      console.error('Benchmark error:', err);
      setError(`Error running optimized benchmark: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setIsRunning(false);
    }
  };

  // Run both benchmarks
  const runBothBenchmarks = async () => {
    await runOriginalBenchmark();
    await runOptimizedBenchmark();
  };

  return (
    <div className="container py-8">
      <h1 className="text-3xl font-bold mb-6">Canvas Performance Benchmark</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Card>
          <CardHeader>
            <CardTitle>Benchmark Configuration</CardTitle>
            <CardDescription>
              Select a scenario and run benchmarks to compare performance
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-1 block">
                  Scenario
                </label>
                <Select
                  value={selectedScenario}
                  onValueChange={setSelectedScenario}
                  disabled={isRunning}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select a scenario" />
                  </SelectTrigger>
                  <SelectContent>
                    {SCENARIOS.map(scenario => (
                      <SelectItem key={scenario.name} value={scenario.name}>
                        {scenario.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
          <CardFooter className="flex flex-col space-y-2">
            <Button
              onClick={runBothBenchmarks}
              disabled={isRunning}
              className="w-full"
            >
              Run Both Benchmarks
            </Button>
            <div className="flex w-full space-x-2">
              <Button
                onClick={runOriginalBenchmark}
                disabled={isRunning}
                variant="outline"
                className="flex-1"
              >
                Original Only
              </Button>
              <Button
                onClick={runOptimizedBenchmark}
                disabled={isRunning}
                variant="outline"
                className="flex-1"
              >
                Optimized Only
              </Button>
            </div>
          </CardFooter>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Benchmark Status</CardTitle>
            <CardDescription>
              {isRunning
                ? 'Running benchmark...'
                : originalResults && optimizedResults
                ? 'Benchmarks completed'
                : originalResults
                ? 'Original benchmark completed'
                : optimizedResults
                ? 'Optimized benchmark completed'
                : 'Ready to run benchmarks'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isRunning && (
              <div className="space-y-2">
                <Progress value={progress} />
                <p className="text-sm text-muted-foreground">
                  Running benchmark... {progress}%
                </p>
              </div>
            )}

            {error && (
              <Alert variant="destructive">
                <AlertTriangleIcon className="h-4 w-4" />
                <AlertTitle>Error</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {!isRunning && !error && (originalResults || optimizedResults) && (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h3 className="text-lg font-semibold mb-2">Original Canvas</h3>
                  {originalResults ? (
                    <div className="text-sm">
                      <p>Total Duration: {originalResults.totalDuration.toFixed(2)}ms</p>
                      {originalResults.fps && (
                        <p>Average FPS: {originalResults.fps.toFixed(2)}</p>
                      )}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">Not run yet</p>
                  )}
                </div>

                <div>
                  <h3 className="text-lg font-semibold mb-2">Optimized Canvas</h3>
                  {optimizedResults ? (
                    <div className="text-sm">
                      <p>Total Duration: {optimizedResults.totalDuration.toFixed(2)}ms</p>
                      {optimizedResults.fps && (
                        <p>Average FPS: {optimizedResults.fps.toFixed(2)}</p>
                      )}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">Not run yet</p>
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {(originalResults || optimizedResults) && (
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="mb-6">
            <TabsTrigger value="results">Results</TabsTrigger>
            <TabsTrigger value="comparison">Comparison</TabsTrigger>
            <TabsTrigger value="details">Detailed Metrics</TabsTrigger>
          </TabsList>

          <TabsContent value="results">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <ResultCard
                title="Total Duration"
                value={optimizedResults?.totalDuration || 0}
                unit="ms"
                improvement={
                  comparison?.totalDuration !== undefined
                    ? comparison.totalDuration
                    : undefined
                }
              />

              <ResultCard
                title="Average FPS"
                value={optimizedResults?.fps || 0}
                unit="fps"
                improvement={
                  comparison?.fps !== undefined ? comparison.fps : undefined
                }
                higherIsBetter={true}
              />

              <ResultCard
                title="Memory Usage"
                value={
                  optimizedResults?.memoryUsage?.diff
                    ? optimizedResults.memoryUsage.diff / (1024 * 1024)
                    : 0
                }
                unit="MB"
                improvement={
                  comparison?.memoryUsage !== undefined
                    ? comparison.memoryUsage
                    : undefined
                }
              />

              <ResultCard
                title="Render Time"
                value={
                  optimizedResults?.metrics?.['benchmark.render']?.average || 0
                }
                unit="ms"
                improvement={
                  comparison?.['benchmark.render.average'] !== undefined
                    ? comparison['benchmark.render.average']
                    : undefined
                }
              />

              <ResultCard
                title="Update Time"
                value={
                  optimizedResults?.metrics?.['benchmark.update']?.average || 0
                }
                unit="ms"
                improvement={
                  comparison?.['benchmark.update.average'] !== undefined
                    ? comparison['benchmark.update.average']
                    : undefined
                }
              />

              <ResultCard
                title="Collaboration Time"
                value={
                  optimizedResults?.metrics?.['benchmark.collaboration']
                    ?.average || 0
                }
                unit="ms"
                improvement={
                  comparison?.['benchmark.collaboration.average'] !== undefined
                    ? comparison['benchmark.collaboration.average']
                    : undefined
                }
              />
            </div>
          </TabsContent>

          <TabsContent value="comparison">
            {comparison ? (
              <Card>
                <CardHeader>
                  <CardTitle>Performance Improvement</CardTitle>
                  <CardDescription>
                    Comparison between original and optimized Canvas
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {Object.entries(comparison).map(([key, value]) => (
                      <div key={key} className="flex justify-between items-center">
                        <span className="font-medium">{key}</span>
                        <span
                          className={
                            Number(value) > 0
                              ? 'text-green-500'
                              : Number(value) < 0
                              ? 'text-red-500'
                              : ''
                          }
                        >
                          {Number(value) > 0 ? '+' : ''}
                          {Number(value).toFixed(2)}%
                        </span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Alert>
                <InfoIcon className="h-4 w-4" />
                <AlertTitle>No comparison available</AlertTitle>
                <AlertDescription>
                  Run both benchmarks to see a comparison
                </AlertDescription>
              </Alert>
            )}
          </TabsContent>

          <TabsContent value="details">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {originalResults && (
                <Card>
                  <CardHeader>
                    <CardTitle>Original Canvas Metrics</CardTitle>
                  </CardHeader>
                  <CardContent className="max-h-96 overflow-y-auto">
                    <div className="space-y-4">
                      {Object.entries(originalResults.metrics).map(
                        ([key, value]: [string, any]) => (
                          <div key={key}>
                            <h4 className="font-semibold mb-1">{key}</h4>
                            <div className="grid grid-cols-2 gap-2 text-sm">
                              <div>Average: {value.average.toFixed(2)}ms</div>
                              <div>Min: {value.min.toFixed(2)}ms</div>
                              <div>Max: {value.max.toFixed(2)}ms</div>
                              <div>Count: {value.count}</div>
                            </div>
                            <Separator className="my-2" />
                          </div>
                        )
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}

              {optimizedResults && (
                <Card>
                  <CardHeader>
                    <CardTitle>Optimized Canvas Metrics</CardTitle>
                  </CardHeader>
                  <CardContent className="max-h-96 overflow-y-auto">
                    <div className="space-y-4">
                      {Object.entries(optimizedResults.metrics).map(
                        ([key, value]: [string, any]) => (
                          <div key={key}>
                            <h4 className="font-semibold mb-1">{key}</h4>
                            <div className="grid grid-cols-2 gap-2 text-sm">
                              <div>Average: {value.average.toFixed(2)}ms</div>
                              <div>Min: {value.min.toFixed(2)}ms</div>
                              <div>Max: {value.max.toFixed(2)}ms</div>
                              <div>Count: {value.count}</div>
                            </div>
                            <Separator className="my-2" />
                          </div>
                        )
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>
        </Tabs>
      )}

      <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-8">
        <div>
          <h2 className="text-xl font-bold mb-4">Original Canvas</h2>
          <div className="border rounded-lg overflow-hidden h-[400px]">
            <Canvas canvasId="benchmark-original" />
          </div>
        </div>

        <div>
          <h2 className="text-xl font-bold mb-4">Optimized Canvas</h2>
          <div className="border rounded-lg overflow-hidden h-[400px]">
            <CollaborativeCanvas canvasId="benchmark-optimized" />
          </div>
        </div>
      </div>
    </div>
  );
}
