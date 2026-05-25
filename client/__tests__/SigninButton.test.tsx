import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import SignInButton from '@features/quiz/components/SignInButton';


describe('SignInButton', () => {
  const mockOnOpen = jest.fn();

  beforeEach(() => {
    mockOnOpen.mockClear();
  });

  it('renders the sign-in button', () => {
    render(<SignInButton onOpen={mockOnOpen} />);
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('calls onOpen when clicked', () => {
    render(<SignInButton onOpen={mockOnOpen} />);
    const button = screen.getByRole('button', { name: /sign in/i });
    fireEvent.click(button);
    expect(mockOnOpen).toHaveBeenCalledTimes(1);
  });
});
