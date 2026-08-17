interface ProgressBarProps {
  progress: number; // 0-1
  stage?: string;
  message?: string;
}

export default function ProgressBar({ progress, stage, message }: ProgressBarProps) {
  const percent = Math.round(progress * 100);

  return (
    <div className="progress-container animate-in">
      <div className="progress-bar-wrapper">
        <div
          className="progress-bar-fill"
          style={{ width: `${percent}%` }}
        />
      </div>
      <div className="progress-info">
        <span className="progress-stage">
          {stage || message || 'Processing...'}
        </span>
        <span className="progress-percent">{percent}%</span>
      </div>
    </div>
  );
}
