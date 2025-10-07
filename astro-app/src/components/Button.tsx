import React from 'react';
import '../styles/global.css';

type ButtonProps = {
  label: string;
  type?: "button" | "submit";
  onClick?: () => void;
  variant?: "primary" | "secondary" | "danger";
  disabled?: boolean;
};

const Button: React.FC<ButtonProps> = ({
  label,
  type = "button",
  onClick,
  variant = "primary",
  disabled = false,
}) => {
  const classes = `button button-${variant} ${disabled ? "button-disabled" : ""}`;

  return (
    <button
      type={type}
      onClick={onClick}
      className={classes}
      disabled={disabled}
    >
      {label}
    </button>
  );
};

export default Button;
