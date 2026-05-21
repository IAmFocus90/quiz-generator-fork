import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import SignUpButton from '@features/quiz/components/SignUpButton';


describe('SignUpButton', () => {
  const mockOnOpen = jest.fn();

  beforeEach(() => {
    mockOnOpen.mockClear();
  });

  it('renders the sign-up button', () => {
    render(<SignUpButton onOpen={mockOnOpen} />);
    expect(screen.getByRole('button', { name: /sign up/i })).toBeInTheDocument();
  });

  it('calls onOpen when clicked', () => {
    render(<SignUpButton onOpen={mockOnOpen} />);
    const button = screen.getByRole('button', { name: /sign up/i });
    fireEvent.click(button);
    expect(mockOnOpen).toHaveBeenCalledTimes(1);
  });
});
