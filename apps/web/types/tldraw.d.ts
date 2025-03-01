declare module '@tldraw/tldraw' {
  export type TDShapeType = string;

  export interface TDShape {
    id: string;
    type: TDShapeType;
    name?: string;
    parentId?: string;
    childIndex?: number;
    point: [number, number];
    size: [number, number];
    rotation?: number;
    isLocked?: boolean;
    opacity?: number;
    props?: Record<string, any>;
  }

  export type TDDocument = {
    id: string;
    name: string;
    version?: number;
    pages?: Record<string, TDPage>;
    pageStates?: Record<string, TDPageState>;
    assets?: Record<string, TDAsset>;
    shapes?: Record<string, TDShape>;
  };

  export type TDPage = {
    id: string;
    name: string;
    childIndex?: number;
    parentId?: string;
    point?: [number, number];
    size?: [number, number];
    shapes: Record<string, TDShape>;
    bindings: Record<string, TDBinding>;
  };

  export type TDBinding = {
    id: string;
    fromId: string;
    toId: string;
    handleId: string;
  };

  export type TDAsset = {
    id: string;
    type: string;
    src: string;
    size: [number, number];
  };

  export type TDPageState = {
    id: string;
    selectedIds: string[];
    backgroundColor?: string;
    camera: {
      point: [number, number];
      zoom: number;
    };
    point?: [number, number];
    size?: [number, number];
  };

  export type TDCamera = {
      point: [number, number];
      zoom: number;
  };

  export interface TldrawProps {
    document?: TDDocument;
    currentPageId?: string;
    showMenu?: boolean;
    showPages?: boolean;
    showStyles?: boolean;
    showTools?: boolean;
    showUI?: boolean;
    readOnly?: boolean;
    disableAssets?: boolean;
    onMount?: (app: TldrawApp) => void;
    onChange?: (state: { document: TDDocument }) => void;
    onChangePageState?: (state: { pageState: TDPageState }) => void;
    onUndo?: () => void;
    onRedo?: () => void;
    onSave?: () => void;
    onSaveAs?: () => void;
    onExport?: () => void;
  }

  export class TldrawApp {
    document: TDDocument;
    inputs: {
      currentPoint: [number, number];
    };

    undo(): void;
    redo(): void;
    zoomIn(): void;
    zoomOut(): void;
    resetZoom(): void;
    resetCamera(): void;
    selectAll(): void;
    clearSelection(): void;
    delete(): void;
    cut(): void;
    copy(): void;
    paste(): void;
    setCurrentPage(pageId: string): void;
    createPage(): void;
    duplicatePage(): void;
    createNewShapeId(): string;
    createShapeId(): string;
    createShape(shape: Partial<TDShape>): void;
    updateShape(shape: Partial<TDShape> & { id: string }): void;
    deleteShape(id: string): void;
    selectShape(id: string): void;
    select(...ids: string[]): void;
    loadDocument(document: TDDocument): void;
    // Two overloads for setPageState
    setPageState(state: Partial<TDPageState>): void;
    setPageState(pageId: string, state: Partial<TDPageState>): void;
    // Method to update page properties
    updatePage(pageId: string, properties: Partial<TDPage>): void;
    registerShapeType(config: any): void;
  }

  export const Tldraw: React.FC<TldrawProps>;
  export const HTMLContainer: React.FC<any>;
}

declare module 'yjs' {
  export class Doc {
    constructor();
    getText(name: string): Text;
    getArray(name: string): Array<any>;
    getMap(name: string): Map<any, any>;
    on(event: string, handler: Function): void;
    off(event: string, handler: Function): void;
    destroy(): void;
  }

  export class Text {
    toString(): string;
    insert(index: number, content: string): void;
    delete(index: number, length: number): void;
    observe(handler: Function): void;
    unobserve(handler: Function): void;
    length: number;
  }

  export class Array<T> {
    push(content: T): void;
    insert(index: number, content: T): void;
    delete(index: number, length: number): void;
    observe(handler: Function): void;
    unobserve(handler: Function): void;
    toArray(): T[];
    length: number;
  }

  export class Map<K, V> {
    set(key: K, value: V): void;
    get(key: K): V | undefined;
    delete(key: K): void;
    observe(handler: Function): void;
    unobserve(handler: Function): void;
    toJSON(): Record<string, V>;
  }
}

declare module 'y-websocket' {
  import { Doc } from 'yjs';

  export interface WebsocketProviderOptions {
    connect?: boolean;
    awareness?: any;
    params?: Record<string, string>;
    WebSocketPolyfill?: any;
    resyncInterval?: number;
    maxBackoffTime?: number;
    disableBc?: boolean;
  }

  export class WebsocketProvider {
    constructor(
      serverUrl: string,
      roomName: string,
      doc: Doc,
      options?: WebsocketProviderOptions
    );

    awareness: {
      getLocalState(): any;
      setLocalStateField(field: string, value: any): void;
      getStates(): Map<number, any>;
      on(event: string, handler: Function): void;
      off(event: string, handler: Function): void;
      clientID: number;
    };

    on(event: string, handler: Function): void;
    off(event: string, handler: Function): void;
    connect(): void;
    disconnect(): void;
    destroy(): void;
  }
}
