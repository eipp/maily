/**
 * Base command interface
 */
export interface Command {
  /**
   * Command type
   */
  readonly type: string;
}

/**
 * Result of a command execution
 */
export interface CommandResult<T = any> {
  /**
   * Whether the command was successful
   */
  success: boolean;

  /**
   * Result data
   */
  data?: T;

  /**
   * Error message if the command failed
   */
  error?: string;

  /**
   * Error code if the command failed
   */
  errorCode?: string;
}

/**
 * Command handler interface
 */
export interface CommandHandler<TCommand extends Command, TResult = any> {
  /**
   * Execute the command
   * @param command Command to execute
   */
  execute(command: TCommand): Promise<CommandResult<TResult>>;
}

/**
 * Command bus interface for dispatching commands
 */
export interface CommandBus {
  /**
   * Register a command handler
   * @param commandType Command type
   * @param handler Command handler
   */
  register<TCommand extends Command, TResult = any>(
    commandType: string,
    handler: CommandHandler<TCommand, TResult>
  ): void;

  /**
   * Execute a command
   * @param command Command to execute
   */
  execute<TCommand extends Command, TResult = any>(
    command: TCommand
  ): Promise<CommandResult<TResult>>;
}

/**
 * In-memory command bus implementation
 */
export class InMemoryCommandBus implements CommandBus {
  private handlers: Map<string, CommandHandler<any, any>> = new Map();

  /**
   * Register a command handler
   * @param commandType Command type
   * @param handler Command handler
   */
  register<TCommand extends Command, TResult = any>(
    commandType: string,
    handler: CommandHandler<TCommand, TResult>
  ): void {
    this.handlers.set(commandType, handler);
  }

  /**
   * Execute a command
   * @param command Command to execute
   */
  async execute<TCommand extends Command, TResult = any>(
    command: TCommand
  ): Promise<CommandResult<TResult>> {
    const handler = this.handlers.get(command.type);

    if (!handler) {
      return {
        success: false,
        error: `No handler registered for command type: ${command.type}`,
        errorCode: 'COMMAND_HANDLER_NOT_FOUND',
      };
    }

    try {
      return await handler.execute(command);
    } catch (error: any) {
      return {
        success: false,
        error: error.message,
        errorCode: error.code || 'COMMAND_EXECUTION_ERROR',
      };
    }
  }
}
