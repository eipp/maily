import { canvasPerformance } from './canvasPerformance';

/**
 * Interface for benchmark scenario configuration
 */
interface BenchmarkScenario {
  name: string;
  shapeCount: number;
  operations: Array<{
    type: 'render' | 'update' | 'collaboration' | 'interaction';
    count: number;
  }>;
}

/**
 * Interface for benchmark results
 */
interface BenchmarkResult {
  scenario: string;
  metrics: {
    [key: string]: {
      average: number;
      min: number;
      max: number;
      total: number;
      count: number;
    };
  };
  totalDuration: number;
  memoryUsage?: {
    before: number;
    after: number;
    diff: number;
  };
  fps?: number;
}

/**
 * Canvas Performance Benchmark utility
 *
 * This utility helps measure and compare performance between different
 * implementations of the Canvas component.
 */
export class CanvasPerformanceBenchmark {
  private scenarios: BenchmarkScenario[] = [];
  private results: BenchmarkResult[] = [];
  private isRunning = false;
  private frameCounter = 0;
  private lastFrameTime = 0;
  private fpsReadings: number[] = [];

  /**
   * Add a benchmark scenario
   */
  public addScenario(scenario: BenchmarkScenario): void {
    this.scenarios.push(scenario);
  }

  /**
   * Run all benchmark scenarios
   */
  public async runBenchmarks(): Promise<BenchmarkResult[]> {
    if (this.isRunning) {
      throw new Error('Benchmark is already running');
    }

    this.isRunning = true;
    this.results = [];

    for (const scenario of this.scenarios) {
      const result = await this.runScenario(scenario);
      this.results.push(result);
    }

    this.isRunning = false;
    return this.results;
  }

  /**
   * Run a single benchmark scenario
   */
  private async runScenario(scenario: BenchmarkScenario): Promise<BenchmarkResult> {
    console.log(`Running benchmark scenario: ${scenario.name}`);

    // Reset performance metrics
    canvasPerformance.reset();

    // Measure memory before
    const memoryBefore = this.getMemoryUsage();

    // Start FPS monitoring
    this.startFpsMonitoring();

    const startTime = performance.now();

    // Run operations
    for (const operation of scenario.operations) {
      await this.runOperation(operation, scenario.shapeCount);
    }

    const endTime = performance.now();

    // Stop FPS monitoring
    this.stopFpsMonitoring();

    // Measure memory after
    const memoryAfter = this.getMemoryUsage();

    // Get performance report
    const report = canvasPerformance.getReport();

    // Calculate average FPS
    const avgFps = this.fpsReadings.length > 0
      ? this.fpsReadings.reduce((sum, fps) => sum + fps, 0) / this.fpsReadings.length
      : undefined;

    // Format results
    const result: BenchmarkResult = {
      scenario: scenario.name,
      metrics: {},
      totalDuration: endTime - startTime,
      fps: avgFps,
      memoryUsage: memoryBefore && memoryAfter ? {
        before: memoryBefore,
        after: memoryAfter,
        diff: memoryAfter - memoryBefore,
      } : undefined,
    };

    // Format metrics
    for (const [key, values] of Object.entries(report.metrics)) {
      if (values.length > 0) {
        const durations = values.map(v => v.duration);
        result.metrics[key] = {
          average: durations.reduce((sum, d) => sum + d, 0) / durations.length,
          min: Math.min(...durations),
          max: Math.max(...durations),
          total: durations.reduce((sum, d) => sum + d, 0),
          count: durations.length,
        };
      }
    }

    return result;
  }

  /**
   * Run a specific operation type
   */
  private async runOperation(
    operation: { type: string; count: number },
    shapeCount: number
  ): Promise<void> {
    switch (operation.type) {
      case 'render':
        await this.simulateRender(operation.count, shapeCount);
        break;
      case 'update':
        await this.simulateUpdates(operation.count, shapeCount);
        break;
      case 'collaboration':
        await this.simulateCollaboration(operation.count, shapeCount);
        break;
      case 'interaction':
        await this.simulateInteractions(operation.count);
        break;
      default:
        console.warn(`Unknown operation type: ${operation.type}`);
    }
  }

  /**
   * Simulate rendering operations
   */
  private async simulateRender(count: number, shapeCount: number): Promise<void> {
    for (let i = 0; i < count; i++) {
      canvasPerformance.startMetric('benchmark.render');

      // Simulate rendering shapes
      const shapes = this.generateShapes(shapeCount);
      this.renderShapes(shapes);

      canvasPerformance.endMetric('benchmark.render');

      // Wait for next frame to avoid blocking UI
      if (i % 10 === 0) {
        await this.nextFrame();
      }
    }
  }

  /**
   * Simulate update operations
   */
  private async simulateUpdates(count: number, shapeCount: number): Promise<void> {
    const shapes = this.generateShapes(shapeCount);

    for (let i = 0; i < count; i++) {
      canvasPerformance.startMetric('benchmark.update');

      // Simulate updating shapes
      this.updateShapes(shapes);

      canvasPerformance.endMetric('benchmark.update');

      // Wait for next frame to avoid blocking UI
      if (i % 10 === 0) {
        await this.nextFrame();
      }
    }
  }

  /**
   * Simulate collaboration operations
   */
  private async simulateCollaboration(count: number, shapeCount: number): Promise<void> {
    const shapes = this.generateShapes(shapeCount);

    for (let i = 0; i < count; i++) {
      canvasPerformance.startMetric('benchmark.collaboration');

      // Simulate collaboration updates
      this.simulateCollaborationUpdate(shapes);

      canvasPerformance.endMetric('benchmark.collaboration');

      // Wait for next frame to avoid blocking UI
      if (i % 10 === 0) {
        await this.nextFrame();
      }
    }
  }

  /**
   * Simulate interaction operations
   */
  private async simulateInteractions(count: number): Promise<void> {
    for (let i = 0; i < count; i++) {
      canvasPerformance.startMetric('benchmark.interaction');

      // Simulate user interactions
      this.simulateUserInteraction();

      canvasPerformance.endMetric('benchmark.interaction');

      // Wait for next frame to avoid blocking UI
      if (i % 10 === 0) {
        await this.nextFrame();
      }
    }
  }

  /**
   * Generate random shapes for testing
   */
  private generateShapes(count: number): any[] {
    const shapes = [];
    const types = ['rect', 'circle', 'line', 'text', 'freehand'];

    for (let i = 0; i < count; i++) {
      const type = types[Math.floor(Math.random() * types.length)];

      const baseShape = {
        id: `shape-${i}`,
        type,
        x: Math.random() * 1000,
        y: Math.random() * 1000,
        fill: `#${Math.floor(Math.random() * 16777215).toString(16)}`,
        stroke: `#${Math.floor(Math.random() * 16777215).toString(16)}`,
        strokeWidth: Math.random() * 5 + 1,
      };

      let shape;

      switch (type) {
        case 'rect':
          shape = {
            ...baseShape,
            width: Math.random() * 100 + 20,
            height: Math.random() * 100 + 20,
          };
          break;
        case 'circle':
          shape = {
            ...baseShape,
            radius: Math.random() * 50 + 10,
          };
          break;
        case 'line':
        case 'freehand':
          const points = [];
          const pointCount = Math.floor(Math.random() * 20) + 2;

          for (let j = 0; j < pointCount; j++) {
            points.push(Math.random() * 100);
            points.push(Math.random() * 100);
          }

          shape = {
            ...baseShape,
            points,
          };
          break;
        case 'text':
          shape = {
            ...baseShape,
            text: 'Sample Text',
            fontSize: Math.random() * 20 + 10,
          };
          break;
      }

      shapes.push(shape);
    }

    return shapes;
  }

  /**
   * Simulate rendering shapes
   */
  private renderShapes(shapes: any[]): void {
    // This is a simulation, so we're just doing some work
    // that's proportional to the number of shapes
    shapes.forEach(shape => {
      // Do some calculations to simulate rendering work
      const area = this.calculateShapeArea(shape);
      const perimeter = this.calculateShapePerimeter(shape);

      // More calculations to simulate work
      const dummy = Math.sqrt(area) * perimeter;

      // Prevent optimization
      if (dummy < 0) {
        console.log('This should never happen');
      }
    });
  }

  /**
   * Simulate updating shapes
   */
  private updateShapes(shapes: any[]): void {
    // Update random properties on shapes
    shapes.forEach(shape => {
      shape.x += (Math.random() - 0.5) * 10;
      shape.y += (Math.random() - 0.5) * 10;

      if (shape.width) {
        shape.width += (Math.random() - 0.5) * 5;
      }

      if (shape.height) {
        shape.height += (Math.random() - 0.5) * 5;
      }

      if (shape.radius) {
        shape.radius += (Math.random() - 0.5) * 5;
      }
    });
  }

  /**
   * Simulate collaboration update
   */
  private simulateCollaborationUpdate(shapes: any[]): void {
    // Simulate serializing and deserializing shapes
    const serialized = JSON.stringify(shapes);
    const deserialized = JSON.parse(serialized);

    // Simulate applying updates
    deserialized.forEach((shape: any, index: number) => {
      if (index % 10 === 0) {
        shape.x += (Math.random() - 0.5) * 20;
        shape.y += (Math.random() - 0.5) * 20;
      }
    });
  }

  /**
   * Simulate user interaction
   */
  private simulateUserInteraction(): void {
    // Simulate mouse movements and clicks
    const x = Math.random() * 1000;
    const y = Math.random() * 1000;

    // Simulate hit testing
    for (let i = 0; i < 100; i++) {
      const testX = x + (Math.random() - 0.5) * 10;
      const testY = y + (Math.random() - 0.5) * 10;

      const distance = Math.sqrt(
        Math.pow(testX - x, 2) + Math.pow(testY - y, 2)
      );

      // Prevent optimization
      if (distance < 0) {
        console.log('This should never happen');
      }
    }
  }

  /**
   * Calculate area of a shape (simulation)
   */
  private calculateShapeArea(shape: any): number {
    switch (shape.type) {
      case 'rect':
        return shape.width * shape.height;
      case 'circle':
        return Math.PI * shape.radius * shape.radius;
      case 'line':
      case 'freehand':
      case 'text':
        return 0;
      default:
        return 0;
    }
  }

  /**
   * Calculate perimeter of a shape (simulation)
   */
  private calculateShapePerimeter(shape: any): number {
    switch (shape.type) {
      case 'rect':
        return 2 * (shape.width + shape.height);
      case 'circle':
        return 2 * Math.PI * shape.radius;
      case 'line':
        if (shape.points && shape.points.length >= 4) {
          const x1 = shape.points[0];
          const y1 = shape.points[1];
          const x2 = shape.points[2];
          const y2 = shape.points[3];
          return Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
        }
        return 0;
      case 'freehand':
        if (shape.points && shape.points.length >= 4) {
          let length = 0;
          for (let i = 0; i < shape.points.length - 2; i += 2) {
            const x1 = shape.points[i];
            const y1 = shape.points[i + 1];
            const x2 = shape.points[i + 2];
            const y2 = shape.points[i + 3];
            length += Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
          }
          return length;
        }
        return 0;
      case 'text':
        return 0;
      default:
        return 0;
    }
  }

  /**
   * Wait for next animation frame
   */
  private nextFrame(): Promise<void> {
    return new Promise(resolve => {
      requestAnimationFrame(() => resolve());
    });
  }

  /**
   * Start monitoring FPS
   */
  private startFpsMonitoring(): void {
    this.frameCounter = 0;
    this.lastFrameTime = performance.now();
    this.fpsReadings = [];

    const measureFps = () => {
      this.frameCounter++;
      const currentTime = performance.now();
      const elapsed = currentTime - this.lastFrameTime;

      // Calculate FPS every second
      if (elapsed >= 1000) {
        const fps = (this.frameCounter * 1000) / elapsed;
        this.fpsReadings.push(fps);

        this.frameCounter = 0;
        this.lastFrameTime = currentTime;
      }

      if (this.isRunning) {
        requestAnimationFrame(measureFps);
      }
    };

    requestAnimationFrame(measureFps);
  }

  /**
   * Stop monitoring FPS
   */
  private stopFpsMonitoring(): void {
    // Nothing to do here, the loop will stop itself
    // when isRunning becomes false
  }

  /**
   * Get current memory usage if available
   */
  private getMemoryUsage(): number | undefined {
    if (window.performance && (performance as any).memory) {
      return (performance as any).memory.usedJSHeapSize;
    }
    return undefined;
  }

  /**
   * Get benchmark results
   */
  public getResults(): BenchmarkResult[] {
    return this.results;
  }

  /**
   * Generate a comparison report between two results
   */
  public compareResults(
    baselineResult: BenchmarkResult,
    optimizedResult: BenchmarkResult
  ): { [key: string]: number } {
    const comparison: { [key: string]: number } = {
      totalDuration: this.calculateImprovement(
        baselineResult.totalDuration,
        optimizedResult.totalDuration
      ),
    };

    // Compare FPS if available
    if (baselineResult.fps && optimizedResult.fps) {
      comparison.fps = this.calculateImprovement(
        optimizedResult.fps,
        baselineResult.fps,
        true
      );
    }

    // Compare memory usage if available
    if (baselineResult.memoryUsage && optimizedResult.memoryUsage) {
      comparison.memoryUsage = this.calculateImprovement(
        baselineResult.memoryUsage.diff,
        optimizedResult.memoryUsage.diff
      );
    }

    // Compare metrics
    const allMetricKeys = new Set([
      ...Object.keys(baselineResult.metrics),
      ...Object.keys(optimizedResult.metrics),
    ]);

    allMetricKeys.forEach(key => {
      const baseline = baselineResult.metrics[key];
      const optimized = optimizedResult.metrics[key];

      if (baseline && optimized) {
        comparison[`${key}.average`] = this.calculateImprovement(
          baseline.average,
          optimized.average
        );

        comparison[`${key}.total`] = this.calculateImprovement(
          baseline.total,
          optimized.total
        );
      }
    });

    return comparison;
  }

  /**
   * Calculate improvement percentage
   *
   * @param baseline The baseline value
   * @param optimized The optimized value
   * @param higherIsBetter Whether higher values are better (e.g., FPS)
   * @returns Improvement percentage (positive means improvement)
   */
  private calculateImprovement(
    baseline: number,
    optimized: number,
    higherIsBetter = false
  ): number {
    if (baseline === 0) return 0;

    if (higherIsBetter) {
      // For metrics where higher is better (e.g., FPS)
      return ((optimized - baseline) / baseline) * 100;
    } else {
      // For metrics where lower is better (e.g., duration)
      return ((baseline - optimized) / baseline) * 100;
    }
  }
}

// Export a singleton instance
export const canvasPerformanceBenchmark = new CanvasPerformanceBenchmark();
