import React from "react";

interface Props {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

/** ErrorBoundary que renderiza fallback (ex: null) em vez de crashar a app. */
export class ErrorBoundaryFallback extends React.Component<
  Props,
  { error: Error | null }
> {
  state = { error: null as Error | null };

  static getDerivedStateFromError(e: Error) {
    return { error: e };
  }

  render() {
    if (this.state.error) {
      return this.props.fallback ?? null;
    }
    return this.props.children;
  }
}
