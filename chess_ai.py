import tkinter as tk
import chess
import math
import random

# ------------------------------
# EVALUATION FUNCTION
# ------------------------------
def evaluate(board):
    """Evaluate board using material, mobility, and center control."""
    piece_values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3.2,
        chess.BISHOP: 3.3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 100
    }

    score = 0

    # --- Material ---
    for piece_type in piece_values:
        score += len(board.pieces(piece_type, chess.WHITE)) * piece_values[piece_type]
        score -= len(board.pieces(piece_type, chess.BLACK)) * piece_values[piece_type]

    # --- Mobility ---
    white_mobility = len(list(board.legal_moves)) if board.turn == chess.WHITE else 0
    board.turn = chess.BLACK
    black_mobility = len(list(board.legal_moves))
    board.turn = not board.turn  # restore
    score += 0.1 * (white_mobility - black_mobility)

    # --- Center Control ---
    center_squares = [chess.D4, chess.D5, chess.E4, chess.E5]
    for sq in center_squares:
        piece = board.piece_at(sq)
        if piece:
            if piece.color == chess.WHITE:
                score += 0.3
            else:
                score -= 0.3

    # --- Reward giving check ---
    if board.is_check():
        score += 0.5

    return score


# ------------------------------
# MINIMAX WITH ALPHA-BETA
# ------------------------------
def minimax(board, depth, alpha, beta, maximizing):
    # Handle terminal states smartly
    if board.is_game_over():
        if board.is_checkmate():
            # If it's white to move and checkmate, that means black won
            return (-9999 if board.turn == chess.WHITE else 9999), None
        elif board.is_stalemate():
            return -200, None  # discourage stalemates
        else:
            return 0, None  # draws, repetition, insufficient material

    if depth == 0:
        return evaluate(board), None

    legal_moves = list(board.legal_moves)
    if not legal_moves:
        return evaluate(board), None

    best_move = None

    if maximizing:
        max_eval = -math.inf
        for move in legal_moves:
            board.push(move)
            eval_score, _ = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        if best_move is None:
            best_move = random.choice(legal_moves)
        return max_eval, best_move
    else:
        min_eval = math.inf
        for move in legal_moves:
            board.push(move)
            eval_score, _ = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        if best_move is None:
            best_move = random.choice(legal_moves)
        return min_eval, best_move


# ------------------------------
# CHESS GUI CLASS
# ------------------------------
class ChessGUI:
    def __init__(self, root):
        self.root = root
        self.board = chess.Board()
        self.square_size = 64
        self.selected_square = None

        # --- GUI Setup ---
        self.canvas = tk.Canvas(root, width=8*self.square_size, height=8*self.square_size)
        self.canvas.pack()
        self.status = tk.Label(root, text="AI (White) is making the first move...", font=("Arial", 14))
        self.status.pack()

        self.symbols = {
            'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚', 'p': '♟',
            'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔', 'P': '♙'
        }

        self.canvas.bind("<Button-1>", self.on_click)
        self.draw_board()

        # AI starts first
        self.root.after(800, self.ai_move)

    # --------------------------
    # DRAW BOARD
    # --------------------------
    def draw_board(self):
        self.canvas.delete("all")
        colors = ["#EEEED2", "#769656"]
        for r in range(8):
            for c in range(8):
                color = colors[(r + c) % 2]
                if self.selected_square == chess.square(c, 7 - r):
                    color = "#BACA44"  # highlight selection
                self.canvas.create_rectangle(
                    c * self.square_size, r * self.square_size,
                    (c + 1) * self.square_size, (r + 1) * self.square_size,
                    fill=color, outline=""
                )
                piece = self.board.piece_at(chess.square(c, 7 - r))
                if piece:
                    self.canvas.create_text(
                        c * self.square_size + self.square_size // 2,
                        r * self.square_size + self.square_size // 2,
                        text=self.symbols[piece.symbol()],
                        font=("Arial", 36)
                    )
        self.root.update()

    # --------------------------
    # PLAYER MOVE (BLACK)
    # --------------------------
    def on_click(self, event):
        if self.board.is_game_over():
            self.status.config(text="Game Over!")
            return

        if self.board.turn != chess.BLACK:
            return  # not your turn

        row = event.y // self.square_size
        col = event.x // self.square_size
        square = chess.square(col, 7 - row)

        if self.selected_square is None:
            piece = self.board.piece_at(square)
            if piece and piece.color == chess.BLACK:
                self.selected_square = square
        else:
            move = chess.Move(self.selected_square, square)
            if move in self.board.legal_moves:
                self.board.push(move)
                self.selected_square = None
                self.draw_board()

                if self.board.is_checkmate():
                    self.status.config(text="You won! (Checkmate)")
                    return
                elif self.board.is_stalemate():
                    self.status.config(text="Draw (Stalemate)")
                    return

                self.status.config(text="AI thinking...")
                self.root.after(500, self.ai_move)
            else:
                self.selected_square = None
        self.draw_board()

    # --------------------------
    # AI MOVE (WHITE)
    # --------------------------
    def ai_move(self):
        if self.board.is_game_over():
            self.status.config(text="Game Over!")
            return

        self.status.config(text="AI thinking...")
        self.root.update()

        _, best_move = minimax(self.board, 3, -math.inf, math.inf, True)

        if best_move:
            self.board.push(best_move)
        self.draw_board()

        if self.board.is_checkmate():
            self.status.config(text="AI wins by checkmate!")
        elif self.board.is_stalemate():
            self.status.config(text="Draw (Stalemate)")
        else:
            self.status.config(text="Your move (Black ♟)")

# ------------------------------
# MAIN FUNCTION
# ------------------------------
def main():
    root = tk.Tk()
    root.title("Chess AI")
    app = ChessGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
