import React from 'react';

interface CardProps {
    children: React.ReactNode;
    className?: string;
    variant?: 'default' | 'glass';
}

export function Card({ children, className = '', variant = 'glass' }: CardProps) {
    const variants = {
        default: 'bg-gray-800 border-gray-700',
        glass: `
      bg-gray-900/40 backdrop-blur-xl
      border border-gray-800/50
      shadow-2xl shadow-black/20
    `,
    };

    return (
        <div
            className={`
        rounded-2xl p-8
        ${variants[variant]}
        ${className}
      `}
        >
            {children}
        </div>
    );
}

interface CardHeaderProps {
    children: React.ReactNode;
    className?: string;
}

export function CardHeader({ children, className = '' }: CardHeaderProps) {
    return (
        <div className={`mb-8 text-center ${className}`}>
            {children}
        </div>
    );
}

interface CardTitleProps {
    children: React.ReactNode;
    className?: string;
}

export function CardTitle({ children, className = '' }: CardTitleProps) {
    return (
        <h2
            className={`
        text-3xl font-bold
        bg-gradient-to-r from-violet-400 to-indigo-400
        bg-clip-text text-transparent
        ${className}
      `}
        >
            {children}
        </h2>
    );
}

interface CardDescriptionProps {
    children: React.ReactNode;
    className?: string;
}

export function CardDescription({ children, className = '' }: CardDescriptionProps) {
    return (
        <p className={`mt-2 text-gray-400 ${className}`}>
            {children}
        </p>
    );
}

interface CardContentProps {
    children: React.ReactNode;
    className?: string;
}

export function CardContent({ children, className = '' }: CardContentProps) {
    return (
        <div className={`space-y-6 ${className}`}>
            {children}
        </div>
    );
}

interface CardFooterProps {
    children: React.ReactNode;
    className?: string;
}

export function CardFooter({ children, className = '' }: CardFooterProps) {
    return (
        <div className={`mt-8 ${className}`}>
            {children}
        </div>
    );
}
