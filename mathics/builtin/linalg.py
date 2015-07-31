# -*- coding: utf8 -*-

"""
Linear algebra
"""

import sympy
import numpy
import scipy


from mathics.builtin.base import Builtin
from mathics.core.convert import from_sympy
from mathics.core.expression import Expression, Integer, Complex, Symbol, Real


def matrix_data(m):
    if not m.has_form('List', None):
        return None
    if all(leaf.has_form('List', None) for leaf in m.leaves):
        return [[item.to_sympy() for item in row.leaves] for row in m.leaves]
    elif not any(leaf.has_form('List', None) for leaf in m.leaves):
        return [item.to_sympy() for item in m.leaves]
    else:
        return None


def to_sympy_matrix(data, **kwargs):
    if not isinstance(data, list):
        data = matrix_data(data)
    try:
        return sympy.Matrix(data)
    except (TypeError, AssertionError, ValueError):
        return None


def numeric_matrix_data(m):
    if not m.has_form('List', None):
        return None
    if all(leaf.has_form('List', None) for leaf in m.leaves):
        return [[item.to_python() for item in row.leaves] for row in m.leaves]
    elif not any(leaf.has_form('List', None) for leaf in m.leaves):
        return [item.to_python() for item in m.leaves]
    else:
        return None

def to_numpy_matrix(data, **kwargs):
    'convert a mathics matrix to a numpy.ndarray object'
    if not isinstance(data, list):
        data = numeric_matrix_data(data)
    try:
        return numpy.array(data)
    except (TypeError, AssertionError, ValueError):
        return None

def is_numeric_Matrix(m,evaluation):
    return Expression("MatrixQ",*[m,Symbol('NumberQ')]).evaluate(evaluation).to_python()
    

class Det(Builtin):
    u"""
    <dl>
    <dt>'Det[$m$]'
        <dd>computes the determinant of the matrix $m$.
    </dl>

    >> Det[{{1, 1, 0}, {1, 0, 1}, {0, 1, 1}}]
     = -2.

    Symbolic determinant:
    >> Det[{{a, b, c}, {d, e, f}, {g, h, i}}]
     = a e i - a f h - b d i + b f g + c d h - c e g
    """
    def apply(self, m, evaluation):
        'Det[m_]'
        if is_numeric_Matrix(m,evaluation):
            matrix = to_numpy_matrix(m)
            if matrix is None or ( len(matrix.shape) !=2 ) or matrix.shape[0] != matrix.shape[1]:
                return evaluation.message('Eigenvalues', 'matsq', m)
            s,lndet= numpy.linalg.slogdet(matrix)
            if s == 0:
                return from_sympy(0.);
            return Expression('Times',*[from_sympy(s),Expression("Exp",*[from_sympy(lndet)])]).evaluate(evaluation)
        else:            # symbolic matrix
            matrix = to_sympy_matrix(m)
            if matrix is None or matrix.cols != matrix.rows or matrix.cols == 0:
                return evaluation.message('Det', 'matsq', m)
            det = matrix.det()
            return from_sympy(det)



class Cross(Builtin):
    """
    <dl>
    <dt>'Cross[$a$, $b$]'
        <dd>computes the vector cross product of $a$ and $b$.
    </dl>

    >> Cross[{x1, y1, z1}, {x2, y2, z2}]
     = {y1 z2 - y2 z1, -x1 z2 + x2 z1, x1 y2 - x2 y1}

    >> Cross[{x, y}]
     = {-y, x}

    >> Cross[{1, 2}, {3, 4, 5}]
     : The arguments are expected to be vectors of equal length, and the number of arguments is expected to be 1 less than their length.
     = Cross[{1, 2}, {3, 4, 5}]
    """

    rules = {
        'Cross[{x_, y_}]': '{-y, x}',
    }

    messages = {
        'nonn1': ('The arguments are expected to be vectors of equal length, '
                  'and the number of arguments is expected to be 1 less than '
                  'their length.'),
    }

    # TODO Vectors of length other than 3

    def apply(self, a, b, evaluation):
        'Cross[a_, b_]'
        a = to_sympy_matrix(a)
        b = to_sympy_matrix(b)
        try:
            res = a.cross(b)
        except sympy.ShapeError:
            return evaluation.message('Cross', 'nonn1')
        return from_sympy(res)


class VectorAngle(Builtin):
    """
    <dl>
    <dt>'VectorAngle[$u$, $v$]'
        <dd>gives the angles between vectors $u$ and $v$
    </dl>

    >> VectorAngle[{1, 0}, {0, 1}]
     = Pi / 2

    >> VectorAngle[{1, 2}, {3, 1}]
     = Pi / 4

    >> VectorAngle[{1, 1, 0}, {1, 0, 1}]
     = Pi / 3

    #> VectorAngle[{0, 1}, {0, 1}]
     = 0
    """

    rules = {
        'VectorAngle[u_, v_]': 'ArcCos[u.v / (Norm[u] Norm[v])]',
    }


class Degree(Builtin):
    """
    <dl>
    <dt>'Degree'
        <dd>is number of radians in one degree.
    </dl>

    >> Cos[60 Degree]
     = 1 / 2
    """

    rules = {
        'Degree': '(Pi/180)'
    }


class Inverse(Builtin):
    """
    <dl>
    <dt>'Inverse[$m$]'
        <dd>computes the inverse of the matrix $m$.
    </dl>

    >> Inverse[{{1, 2, 0}, {2, 3, 0}, {3, 4, 1}}]
     = {{-3, 2, 0}, {2, -1, 0}, {1, -2, 1}}
    >> Inverse[{{1, 0}, {0, 0}}]
     : The matrix {{1, 0}, {0, 0}} is singular.
     = Inverse[{{1, 0}, {0, 0}}]

    >> Inverse[{{1, 0, 0}, {0, Sqrt[3]/2, 1/2}, {0,-1 / 2, Sqrt[3]/2}}]
    = {{1, 0, 0}, {0, Sqrt[3] / 2, -1 / 2}, {0, 1 / 2, Sqrt[3] / 2}}
    """

    messages = {
        'sing': "The matrix `1` is singular.",
    }

    def apply(self, m, evaluation):
        'Inverse[m_]'
        if is_numeric_Matrix(m,evaluation):
            matrix = to_numpy_matrix(m)
            if matrix is None or ( len(matrix.shape) !=2 ) or matrix.shape[0] != matrix.shape[1]:
                return evaluation.message('Inverse', 'matsq', m)
            try:
                res=scipy.linalg.inv(matrix)
                return from_sympy(res)
            except scipy.linalg.LinAlgError as err:
#              print "exception:"
               if str(err) == "Singular matrix":
                   return evaluation.message('Inverse', 'sing', m)
               else:
                   raise(err)
        else:            # symbolic matrix
            matrix = to_sympy_matrix(m)
            if matrix is None or matrix.cols != matrix.rows or matrix.cols == 0:
                return evaluation.message('Inverse', 'matsq', m)
            if matrix.det() == 0:
                return evaluation.message('Inverse', 'sing', m)
            inv = matrix.inv()
            return from_sympy(inv)





        matrix = to_sympy_matrix(m)
        if matrix is None or matrix.cols != matrix.rows or matrix.cols == 0:
            return evaluation.message('Inverse', 'matsq', m)
        if matrix.det() == 0:
            return evaluation.message('Inverse', 'sing', m)
        inv = matrix.inv()
        return from_sympy(inv)


class LinearSolve(Builtin):
    """
    <dl>
    <dt>'LinearSolve[$matrix$, $right$]'
        <dd>solves the linear equation system '$matrix$ . x = $right$' and returns one corresponding solution 'x'.
    </dl>

    >> LinearSolve[{{1, 1, 0}, {1, 0, 1}, {0, 1, 1}}, {1, 2, 3}]
     = {0, 1, 2}
    Test the solution:
    >> {{1, 1, 0}, {1, 0, 1}, {0, 1, 1}} . {0, 1, 2}
     = {1, 2, 3}
    If there are several solutions, one arbitrary solution is returned:
    >> LinearSolve[{{1, 2, 3}, {4, 5, 6}, {7, 8, 9}}, {1, 1, 1}]
     = {-1, 1, 0}
    Infeasible systems are reported:
    >> LinearSolve[{{1, 2, 3}, {4, 5, 6}, {7, 8, 9}}, {1, -2, 3}]
     : Linear equation encountered that has no solution.
     = LinearSolve[{{1, 2, 3}, {4, 5, 6}, {7, 8, 9}}, {1, -2, 3}]
    """

    messages = {
        'lslc': ("Coefficient matrix and target vector(s) or matrix "
                 "do not have the same dimensions."),
        'nosol': "Linear equation encountered that has no solution.",
    }

    def apply(self, m, b, evaluation):
        'LinearSolve[m_, b_]'

        matrix = matrix_data(m)
        if matrix is None:
            return
        if not b.has_form('List', None):
            return
        if len(b.leaves) != len(matrix):
            return evaluation.message('LinearSolve', 'lslc')
        system = [mm + [v] for mm, v in zip(matrix, b.leaves)]
        system = to_sympy_matrix(system)
        if system is None:
            return
        syms = [sympy.Dummy('LinearSolve_var%d' % k)
                for k in range(system.cols - 1)]
        sol = sympy.solve_linear_system(system, *syms)
        if sol:
            # substitute 0 for variables that are not in result dictionary
            free_vars = dict((sym, sympy.Integer(
                0)) for sym in syms if sym not in sol)
            sol.update(free_vars)
            sol = [(sol[sym] if sym in free_vars else sol[sym].subs(free_vars))
                   for sym in syms]
            return from_sympy(sol)
        else:
            return evaluation.message('LinearSolve', 'nosol')


class NullSpace(Builtin):
    """
    <dl>
    <dt>'NullSpace[$matrix$]'
        <dd>returns a list of vectors that span the nullspace of $matrix$.
    </dl>

    >> NullSpace[{{1, 2, 3}, {4, 5, 6}, {7, 8, 9}}]
     = {{1, -2, 1}}

    >> A = {{1, 1, 0}, {1, 0, 1}, {0, 1, 1}};
    >> NullSpace[A]
     = {}
    >> MatrixRank[A]
     = 3
    """

    def apply(self, m, evaluation):
        'NullSpace[m_]'

        matrix = to_sympy_matrix(m)
        if matrix is None:
            return
        nullspace = matrix.nullspace()
        # convert n x 1 matrices to vectors
        nullspace = [list(vec) for vec in nullspace]
        return from_sympy(nullspace)


class RowReduce(Builtin):
    """
    <dl>
    <dt>'RowReduce[$matrix$]'
        <dd>returns the reduced row-echelon form of $matrix$.
    </dl>

    >> RowReduce[{{1, 0, a}, {1, 1, b}}]
     = {{1, 0, a}, {0, 1, -a + b}}

    >> RowReduce[{{1, 2, 3}, {4, 5, 6}, {7, 8, 9}}] // MatrixForm
     = 1   0   -1
     .
     . 0   1   2
     .
     . 0   0   0

    #> RowReduce[{{1, 0}, {0}}]
     = RowReduce[{{1, 0}, {0}}]
    """

    def apply(self, m, evaluation):
        'RowReduce[m_]'

        matrix = to_sympy_matrix(m)
        if matrix is None:
            return
        reduced = matrix.rref()[0]
        return from_sympy(reduced)


class MatrixRank(Builtin):
    """
    <dl>
    <dt>'MatrixRank[$matrix$]'
        <dd>returns the rank of $matrix$.
    </dl>

    >> MatrixRank[{{1, 2, 3}, {4, 5, 6}, {7, 8, 9}}]
     = 2
    >> MatrixRank[{{1, 1, 0}, {1, 0, 1}, {0, 1, 1}}]
     = 3
    >> MatrixRank[{{a, b}, {3 a, 3 b}}]
     = 1
    """

    def apply(self, m, evaluation):
        'MatrixRank[m_]'

        matrix = to_sympy_matrix(m)
        if matrix is None:
            return
        rank = len(matrix.rref()[1])
        return Integer(rank)


class Eigenvalues(Builtin):
    """
    <dl>
    <dt>'Eigenvalues[$m$]'
        <dd>computes the eigenvalues of the matrix $m$.
    </dl>

    >> Eigenvalues[{{1, 1, 0}, {1, 0, 1}, {0, 1, 1}}] // Sort
     = {-1, 1, 2}

    >> Eigenvalues[{{Cos[theta],Sin[theta],0},{-Sin[theta],Cos[theta],0},{0,0,1}}] // Sort
     = {1, Cos[theta] + Sqrt[-1 + Cos[theta] ^ 2], Cos[theta] - Sqrt[-1 + Cos[theta] ^ 2]}

    >> Eigenvalues[{{7, 1}, {-4, 3}}]
     = {5, 5}
    """

    def apply(self, m, evaluation):
        'Eigenvalues[m_]'

        matrix = to_sympy_matrix(m)
        if matrix is None or matrix.cols != matrix.rows or matrix.cols == 0:
            return evaluation.message('Eigenvalues', 'matsq', m)
        eigenvalues = matrix.eigenvals()
        try:
            eigenvalues = sorted(eigenvalues.iteritems(),
                                 key=lambda (v, c): (abs(v), -v), reverse=True)
        except TypeError as e:
            if not str(e).startswith('cannot determine truth value of'):
                raise e
            eigenvalues = eigenvalues.items()
        return from_sympy([v for (v, c) in eigenvalues for _ in xrange(c)])


class Eigensystem(Builtin):
    """
    <dl>
    <dt>'Eigensystem[$m$]'
        <dd>returns a list of {Eigenvalues, Eigenvectors}.
    </dl>

    >> Eigenvalues[{{1, 1, 0}, {1, 0, 1}, {0, 1, 1}}] // Sort
     = {-1, 1, 2}

    >> Eigenvalues[{{Cos[theta],Sin[theta],0},{-Sin[theta],Cos[theta],0},{0,0,1}}] // Sort
     = {1, Cos[theta] + Sqrt[-1 + Cos[theta] ^ 2], Cos[theta] - Sqrt[-1 + Cos[theta] ^ 2]}

    >> Eigenvalues[{{7, 1}, {-4, 3}}]
     = {5, 5}
    """

    rules = {
        'Eigensystem[m_]': '{Eigenvalues[m], Eigenvectors[m]}'
    }


class MatrixPower(Builtin):
    """
    <dl>
    <dt>'MatrixPower[$m$, $n$]'
        <dd>computes the $n$th power of a matrix $m$.
    </dl>

    >> MatrixPower[{{1, 2}, {1, 1}}, 10]
     = {{3363, 4756}, {2378, 3363}}

    >> MatrixPower[{{1, 2}, {2, 5}}, -3]
     = {{169, -70}, {-70, 29}}

    #> MatrixPower[{{0, x}, {0, 0}}, n]
     : Matrix power only implemented for real and integer values.
     = MatrixPower[{{0, x}, {0, 0}}, n]
    """

    messages = {
        'matrixpowernotimplemented': ('Matrix power only implemented for real and integer values.')
    }

    def apply(self, m, power, evaluation):
        'MatrixPower[m_, power_]'
        m = to_sympy_matrix(m)
        try:
            res = m ** power.to_sympy()
        except NotImplementedError:
            return evaluation.message('MatrixPower', 'matrixpowernotimplemented')
        return from_sympy(res)


class MatrixExp(Builtin):
    """
    <dl>
    <dt>'MatrixExp[$m$]'
        <dd>computes the exponential of the matrix $m$.
    </dl>

    >> MatrixExp[{{0, 2}, {0, 1}}]
     = {{1, -2 + 2 E}, {0, E}}

    >> MatrixExp[{{1.5, 0.5}, {0.5, 2.0}}]
     = {{5.16266024276223, 3.029519834622}, {3.029519834622, 8.19218007738423}}

    #> MatrixExp[{{a, 0}, {0, b}}]
     : Matrix exp only implemented for real and integer values.
     = MatrixExp[{{a, 0}, {0, b}}]
    """

    messages = {
        'matrixexpnotimplemented': ('Matrix exp only implemented for real and integer values.')
    }

    # TODO fix precision

    def apply(self, m, evaluation):
        'MatrixExp[m_]'
        m = to_sympy_matrix(m)
        try:
            res = m.exp()
        except NotImplementedError:
            return evaluation.message('MatrixExp', 'matrixexpnotimplemented')
        return from_sympy(res)


class Norm(Builtin):
    """
    <dl>
    <dt>'Norm[$m$, $l$]'</dt>
        <dd>computes the l-norm of matrix m (currently only works for vectors!).</dd>
    <dt>'Norm[$m$]'</dt>
        <dd>computes the 2-norm of matrix m (currently only works for vectors!).</dd>
    </dl>

    >> Norm[{1, 2, 3, 4}, 2]
     = Sqrt[30]

    >> Norm[{10, 100, 200}, 1]
     = 310

    >> Norm[{a, b, c}]
     = Sqrt[Abs[a] ^ 2 + Abs[b] ^ 2 + Abs[c] ^ 2]

    >> Norm[{-100, 2, 3, 4}, Infinity]
     = 100

    >> Norm[1 + I]
     = Sqrt[2]

    #> Norm[{1, {2, 3}}]
     : The first Norm argument should be a number, vector, or matrix.
     = Norm[{1, {2, 3}}]

    #> Norm[{x, y}]
     = Sqrt[Abs[x] ^ 2 + Abs[y] ^ 2]

    #> Norm[{x, y}, p]
     = (Abs[x] ^ p + Abs[y] ^ p) ^ (1 / p)

    #> Norm[{x, y}, 0]
     : The second argument of Norm, 0, should be a symbol, Infinity, or an integer or real number not less than 1 for vector p-norms; or 1, 2, Infinity, or "Frobenius" for matrix norms.
     = Norm[{x, y}, 0]

    #> Norm[{x, y}, 0.5]
     : The second argument of Norm, 0.5, should be a symbol, Infinity, or an integer or real number not less than 1 for vector p-norms; or 1, 2, Infinity, or "Frobenius" for matrix norms.
     = Norm[{x, y}, 0.5]

    #> Norm[{}]
     = Norm[{}]

    #> Norm[0]
     = 0
    """

    rules = {
        'Norm[m_?NumberQ]': 'Abs[m]',
        'Norm[m_, DirectedInfinity[1]]': 'Max[Abs[m]]',
    }

    messages = {
        'nvm': 'The first Norm argument should be a number, vector, or matrix.',
        'ptype': (
            'The second argument of Norm, `1`, should be a symbol, Infinity, '
            'or an integer or real number not less than 1 for vector p-norms; '
            'or 1, 2, Infinity, or "Frobenius" for matrix norms.'),
        'normnotimplemented': 'Norm is not yet implemented for matrices.',
    }

    def apply_single(self, m, evaluation):
        'Norm[m_]'
        return self.apply(m, Integer(2), evaluation)

    def apply(self, m, l, evaluation):
        'Norm[m_, l_]'


        if isinstance(l, Symbol):
            pass
        elif isinstance(l, (Real, Integer)) and l.to_python() >= 1:
            pass
        else:
            return evaluation.message('Norm', 'ptype', l)

        l = l.to_sympy()
        matrix = to_sympy_matrix(m)

        if matrix is None:
            return evaluation.message('Norm', 'nvm')
        if len(matrix) == 0:
            return

        try:
            res = matrix.norm(l)
        except NotImplementedError:
            return evaluation.message('Norm', 'normnotimplemented')

        return from_sympy(res)


class Normalize(Builtin):
    """
    <dl>
    <dt>'Normalize[$v$]'
        <dd>calculates the normalized vector $v$.
    <dt>'Normalize[$z$]'
        <dd>calculates the normalized complex number $z$.
    </dl>

    >> Normalize[{1, 1, 1, 1}]
     = {1 / 2, 1 / 2, 1 / 2, 1 / 2}

    >> Normalize[1 + I]
     = (1 / 2 + I / 2) Sqrt[2]

    #> Normalize[0]
     = 0

    #> Normalize[{0}]
     = {0}

    #> Normalize[{}]
     = {}
    """

    rules = {
        'Normalize[v_]': 'Module[{norm = Norm[v]}, If[norm == 0, v, v / norm, v]]',
    }


class Eigenvectors(Builtin):
    """
    <dl>
    <dt>'Eigenvectors[$m$]'
        <dd>computes the eigenvectors of the matrix $m$.
    </dl>

    >> Eigenvectors[{{1, 1, 0}, {1, 0, 1}, {0, 1, 1}}]
     = {{1, 1, 1}, {1, -2, 1}, {-1, 0, 1}}
    >> Eigenvectors[{{1, 0, 0}, {0, 1, 0}, {0, 0, 0}}]
     = {{0, 1, 0}, {1, 0, 0}, {0, 0, 1}}
    >> Eigenvectors[{{2, 0, 0}, {0, -1, 0}, {0, 0, 0}}]
     = {{1, 0, 0}, {0, 1, 0}, {0, 0, 1}}
    >> Eigenvectors[{{0.1, 0.2}, {0.8, 0.5}}]
     = {{0.309016994374947, 1.}, {-0.809016994374947, 1.}}

    #> Eigenvectors[{{-2, 1, -1}, {-3, 2, 1}, {-1, 1, 0}}]
     = {{1 / 3, 7 / 3, 1}, {1, 1, 0}, {0, 0, 0}}
    """

    messages = {
        'eigenvecnotimplemented': (
            "Eigenvectors is not yet implemented for the matrix `1`."),
    }

    # TODO: Normalise the eigenvectors

    def apply(self, m, evaluation):
        'Eigenvectors[m_]'

        matrix = to_sympy_matrix(m)
        if matrix is None or matrix.cols != matrix.rows or matrix.cols == 0:
            return evaluation.message('Eigenvectors', 'matsq', m)
        # sympy raises an error for some matrices that Mathematica can compute.
        try:
            eigenvects = matrix.eigenvects()
        except NotImplementedError:
            return evaluation.message(
                'Eigenvectors', 'eigenvecnotimplemented', m)

        # The eigenvectors are given in the same order as the eigenvalues.
        eigenvects = sorted(eigenvects, key=lambda (
            val, c, vect): (abs(val), -val), reverse=True)
        result = []
        for val, count, basis in eigenvects:
            # Select the i'th basis vector, convert matrix to vector,
            # and convert from sympy
            vects = [from_sympy(list(b)) for b in basis]

            # This follows Mathematica convention better; higher indexed pivots
            # are outputted first. e.g. {{0,1},{1,0}} instead of {{1,0},{0,1}}
            vects.reverse()

            # Add the vectors to results
            result.extend(vects)
        result.extend([Expression('List', *(
            [0] * matrix.rows))] * (matrix.rows - len(result)))
        return Expression('List', *result)
