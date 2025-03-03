/// <reference types="node" />
/// <reference types="react" />
/// <reference types="react-dom" />

declare namespace NodeJS {
  interface ProcessEnv {
    readonly NODE_ENV: 'development' | 'production' | 'test';
    readonly NEXT_PUBLIC_APP_URL: string;
    readonly NEXT_PUBLIC_LANDING_URL: string;
    readonly NEXT_PUBLIC_API_URL: string;
    readonly NEXT_PUBLIC_ANALYTICS_URL: string;
    readonly NEXT_PUBLIC_CDN_URL: string;
    readonly NEXT_PUBLIC_ENABLE_AI_MESH: string;
    readonly NEXT_PUBLIC_ENABLE_TRUST_VERIFICATION: string;
    readonly NEXT_PUBLIC_ENABLE_REAL_TIME_COLLABORATION: string;
    readonly NEXT_PUBLIC_ANALYTICS_ENABLED: string;
    readonly NEXT_PUBLIC_SENTRY_DSN: string;
    readonly NEXT_PUBLIC_APP_VERSION: string;
    readonly API_URL: string;
    readonly API_KEY: string;
    readonly NEXTAUTH_URL: string;
    readonly NEXTAUTH_SECRET: string;
  }
}

declare module '*.svg' {
  import * as React from 'react';
  export const ReactComponent: React.FunctionComponent<
    React.SVGProps<SVGSVGElement> & { title?: string }
  >;
  const src: string;
  export default src;
}

declare module '*.png' {
  const content: string;
  export default content;
}

declare module '*.jpg' {
  const content: string;
  export default content;
}

declare module '*.jpeg' {
  const content: string;
  export default content;
}

declare module '*.gif' {
  const content: string;
  export default content;
}

declare module '*.webp' {
  const content: string;
  export default content;
}

declare module '*.avif' {
  const content: string;
  export default content;
}

declare module '*.ico' {
  const content: string;
  export default content;
}

declare module '*.json' {
  const content: any;
  export default content;
}
