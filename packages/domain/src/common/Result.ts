/**
 * A Result object represents the outcome of an operation.
 * It can be either successful or failed, and can contain a value or an error.
 */
export class Result<T, E = Error> {
  private readonly _isSuccess: boolean;
  private readonly _value?: T;
  private readonly _error?: E;

  private constructor(isSuccess: boolean, value?: T, error?: E) {
    this._isSuccess = isSuccess;
    this._value = value;
    this._error = error;
  }

  /**
   * Returns true if the result is successful.
   */
  public isSuccess(): boolean {
    return this._isSuccess;
  }

  /**
   * Returns true if the result is a failure.
   */
  public isFailure(): boolean {
    return !this._isSuccess;
  }

  /**
   * Gets the value of a successful result.
   * Throws an error if the result is a failure.
   */
  public getValue(): T {
    if (!this._isSuccess) {
      throw new Error('Cannot get value of a failed result');
    }
    return this._value as T;
  }

  /**
   * Gets the error of a failed result.
   * Throws an error if the result is successful.
   */
  public getError(): E {
    if (this._isSuccess) {
      throw new Error('Cannot get error of a successful result');
    }
    return this._error as E;
  }

  /**
   * Creates a successful result with a value.
   */
  public static success<T, E = Error>(value?: T): Result<T, E> {
    return new Result<T, E>(true, value);
  }

  /**
   * Creates a failed result with an error.
   */
  public static failure<T, E = Error>(error: E): Result<T, E> {
    return new Result<T, E>(false, undefined, error);
  }

  /**
   * Maps the value of a successful result using a mapping function.
   * Returns the same failed result if the result is a failure.
   */
  public map<U>(fn: (value: T) => U): Result<U, E> {
    if (this.isFailure()) {
      return Result.failure<U, E>(this._error as E);
    }
    return Result.success<U, E>(fn(this._value as T));
  }

  /**
   * Applies a function that returns a Result to the value of a successful result.
   * Returns the same failed result if the result is a failure.
   */
  public flatMap<U>(fn: (value: T) => Result<U, E>): Result<U, E> {
    if (this.isFailure()) {
      return Result.failure<U, E>(this._error as E);
    }
    return fn(this._value as T);
  }
}