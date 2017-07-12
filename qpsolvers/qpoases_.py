#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2016-2017 Stephane Caron <stephane.caron@normalesup.org>
#
# This file is part of qpsolvers.
#
# qpsolvers is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# qpsolvers is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# qpsolvers. If not, see <http://www.gnu.org/licenses/>.

from numpy import array, hstack, ones, vstack, zeros
from qpoases import PyOptions as Options
from qpoases import PyPrintLevel as PrintLevel
from qpoases import PyQProblem as QProblem
from qpoases import PyQProblemB as QProblemB
from qpoases import PyReturnValue as ReturnValue
from warnings import warn


__infty = 1e10
options = Options()
options.printLevel = PrintLevel.NONE


def qpoases_solve_qp(P, q, G=None, h=None, A=None, b=None, initvals=None):
    """
    Solve a Quadratic Program defined as:

        minimize
            (1/2) * x.T * P * x + q.T * x

        subject to
            G * x <= h
            A * x == b

    using qpOASES <https://projects.coin-or.org/qpOASES>.

    Parameters
    ----------
    P : array, shape=(n, n)
        Primal quadratic cost matrix.
    q : array, shape=(n,)
        Primal quadratic cost vector.
    G : array, shape=(m, n)
        Linear inequality constraint matrix.
    h : array, shape=(m,)
        Linear inequality constraint vector.
    A : array, shape=(meq, n), optional
        Linear equality constraint matrix.
    b : array, shape=(meq,), optional
        Linear equality constraint vector.
    initvals : array, shape=(n,), optional
        Warm-start guess vector.

    Returns
    -------
    x : array, shape=(n,)
        Solution to the QP, if found, otherwise ``None``.

    Note
    ----
    This function relies on some updates from the standard distribution of
    qpOASES (details below). A fully compatible repository is published at
    <https://github.com/stephane-caron/qpOASES>.

    Note
    ----
    This function allows empty bounds (lb, ub, lbA or ubA). This was provisioned
    by the C++ API but not by the Python API of qpOASES (as of version 3.2.0).
    Be sure to update the Cython file (qpoases.pyx) to convert ``None`` to the
    null pointer, as done e.g. in
    <https://github.com/stephane-caron/qpOASES/commit/207996802f33da2375dd2db5cf58a977ac2bb0d2>
    """
    if initvals is not None:
        warn("[qpsolvers] warm-start values ignored by qpOASES wrapper")
    n = P.shape[0]
    lb, ub = None, None
    nb_wsr = array([100])  # number of working set recalculations
    has_cons = G is not None or A is not None
    if G is not None and A is None:
        C = G
        lb_C = None  # NB:
        ub_C = h
    elif G is None and A is not None:
        C = vstack([A, A])
        lb_C = h
        ub_C = h
    elif G is not None and A is not None:
        C = vstack([G, A, A])
        lb_C = hstack([-__infty * ones(h.shape[0]), b])
        ub_C = hstack([h, b])
    if has_cons:
        qp = QProblem(n, C.shape[0])
        qp.setOptions(options)
        return_value = qp.init(P, q, C, lb, ub, lb_C, ub_C, nb_wsr)
        if return_value == ReturnValue.MAX_NWSR_REACHED:
            warn("qpOASES reached the maximum number of WSR (%d)" % nb_wsr[0])
    else:
        qp = QProblemB(n)
        qp.setOptions(options)
        qp.init(P, q, lb, ub, nb_wsr)
    x_opt = zeros(n)
    qp.getPrimalSolution(x_opt)
    return x_opt
