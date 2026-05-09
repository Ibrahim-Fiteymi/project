/**
 * Error boundary that catches render-time exceptions in any child route
 * and surfaces a friendly recovery UI instead of a blank page.
 */

import { Component, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: { componentStack: string }) {
    // eslint-disable-next-line no-console
    console.error("[ErrorBoundary]", error, info.componentStack);
  }

  reset = () => this.setState({ error: null });

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div className="page">
        <section className="panel error-panel">
          <h2 className="panel-title">Something went wrong.</h2>
          <p className="panel-sub">
            The application hit an unexpected error. You can try again or refresh the page.
          </p>
          <pre className="error-stack">{this.state.error.message}</pre>
          <div className="inline-actions-buttons">
            <button type="button" className="btn" onClick={this.reset}>
              Try again
            </button>
            <button
              type="button"
              className="btn-ghost"
              onClick={() => location.reload()}
            >
              Reload page
            </button>
          </div>
        </section>
      </div>
    );
  }
}
