import { Quiz } from "@features/quiz/types";

export interface DisplayQuizProps {
  quiz: Quiz | null;
}

export interface SharePageProps {
  quiz: Quiz | null;
  notFoundQuiz?: boolean;
}
