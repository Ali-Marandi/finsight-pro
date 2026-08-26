"""
Graph Theory & Network Analysis Engine for FinSight Pro.

Provides correlation network construction, minimum spanning trees,
financial contagion simulation, and systemic risk metrics.
All computations are offline/local using numpy and scipy.
"""

import numpy as np
from scipy import stats, spatial, sparse, linalg


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_native(obj):
    """Recursively convert numpy types to native Python types."""
    if isinstance(obj, np.ndarray):
        return [_to_native(x) for x in obj.tolist()]
    if isinstance(obj, (np.floating, np.float64, np.float32)):
        return round(float(obj), 6)
    if isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    if isinstance(obj, dict):
        return {k: _to_native(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_native(x) for x in obj]
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    return obj


def _r(v, decimals=4):
    """Round a float to the given number of decimal places."""
    return round(float(v), decimals)


def _symmetrize(M):
    """Ensure a matrix is symmetric."""
    return (M + M.T) / 2.0


# ---------------------------------------------------------------------------
# 1. Correlation Network
# ---------------------------------------------------------------------------

def _compute_betweenness_centrality(adj):
    """Compute unweighted betweenness centrality using Brandes' algorithm (simplified)."""
    n = adj.shape[0]
    betweenness = np.zeros(n)

    for s in range(n):
        # BFS shortest-path counting from s
        S = []  # stack
        P = [[] for _ in range(n)]  # predecessors
        sigma = np.zeros(n)
        sigma[s] = 1.0
        d = -np.ones(n)
        d[s] = 0.0
        Q = [s]  # queue

        while Q:
            v = Q.pop(0)
            S.append(v)
            neighbors = np.where(adj[v] > 0)[0]
            for w in neighbors:
                if d[w] < 0:
                    Q.append(w)
                    d[w] = d[v] + 1.0
                if abs(d[w] - d[v] - 1.0) < 1e-10:
                    sigma[w] += sigma[v]
                    P[w].append(v)

        # Back-propagation of dependencies
        delta = np.zeros(n)
        while S:
            w = S.pop()
            for v in P[w]:
                delta[v] += (sigma[v] / sigma[w]) * (1.0 + delta[w])
            if w != s:
                betweenness[w] += delta[w]

    # Normalize (undirected: divide by 2, except for trivial graphs)
    if n > 2:
        betweenness /= 2.0
    return betweenness


def _compute_eigenvector_centrality(adj, max_iter=200, tol=1e-8):
    """Compute eigenvector centrality via power iteration."""
    n = adj.shape[0]
    x = np.ones(n) / np.sqrt(n)

    for _ in range(max_iter):
        x_new = adj @ x
        norm = np.linalg.norm(x_new)
        if norm < 1e-12:
            return np.zeros(n)
        x_new = x_new / norm
        if np.linalg.norm(x_new - x) < tol:
            break
        x = x_new
    return x_new


def _compute_pagerank(adj, d=0.85, max_iter=200, tol=1e-8):
    """Compute PageRank on a weighted adjacency matrix."""
    n = adj.shape[0]
    out_degree = adj.sum(axis=1)

    # Handle dangling nodes (no outgoing edges)
    dangling = (out_degree == 0)
    out_degree[dangling] = 1.0  # avoid division by zero

    # Transition matrix
    M = adj / out_degree[:, np.newaxis]

    # Dangling node adjustment
    dangling_sum = M[dangling].sum(axis=0)

    pr = np.ones(n) / n
    for _ in range(max_iter):
        pr_new = d * (M.T @ pr + dangling_sum * pr.sum() / n) + (1 - d) / n
        if np.linalg.norm(pr_new - pr) < tol:
            break
        pr = pr_new
    return pr


def _louvain_community_detection(adj, max_iter=100):
    """
    Simple Louvain-like greedy modularity optimization.

    Phase 1: Iteratively move each node to the community that maximizes
    modularity gain.  Phase 2 (simplified): one pass is sufficient for
    a good partition in most financial networks.
    """
    n = adj.shape[0]
    m = adj.sum() / 2.0  # total edge weight (undirected)
    if m < 1e-12:
        return list(range(n)), 0.0

    # Convert to positive weighted adjacency
    W = np.abs(adj)
    node_strength = W.sum(axis=1)  # row sums = weighted degree

    # Initialize: each node in its own community
    community = list(range(n))

    def _modularity_gain(node, target_comm, current_comm):
        """Compute modularity gain of moving node from current_comm to target_comm."""
        sigma_in = 0.0  # sum of weights inside target community
        sigma_tot = 0.0  # sum of degrees of nodes in target community
        k_i = node_strength[node]

        # Compute sigma_in and sigma_tot for target community
        members = [j for j in range(n) if community[j] == target_comm]
        for j in members:
            sigma_tot += node_strength[j]
            for k in members:
                sigma_in += W[j, k]

        # Compute sigma_tot for current community (excluding the moving node)
        sigma_tot_curr = 0.0
        curr_members = [j for j in range(n) if community[j] == current_comm and j != node]
        for j in curr_members:
            sigma_tot_curr += node_strength[j]

        # Sum of weights from node to target community
        k_i_in = sum(W[node, j] for j in members)

        # Sum of weights from node to current community (excluding self)
        k_i_curr = sum(W[node, j] for j in curr_members)

        delta_q = (
            k_i_in - sigma_tot * k_i / (2.0 * m)
        ) - (
            k_i_curr - sigma_tot_curr * k_i / (2.0 * m)
        )
        return delta_q

    def _total_modularity(comm_assignment):
        """Compute total modularity Q."""
        unique_comms = set(comm_assignment)
        Q = 0.0
        for c in unique_comms:
            members = [j for j in range(n) if comm_assignment[j] == c]
            l_c = sum(W[i, j] for i in members for j in members)
            d_c = sum(node_strength[j] for j in members)
            Q += l_c / (2.0 * m) - (d_c / (2.0 * m)) ** 2
        return Q

    # Greedy optimization
    improved = True
    iteration = 0
    while improved and iteration < max_iter:
        improved = False
        iteration += 1
        for node in range(n):
            current_comm = community[node]
            best_comm = current_comm
            best_gain = 0.0

            # Gather candidate communities: neighbors' communities + own
            neighbors = set(np.where(W[node] > 0)[0].tolist())
            candidates = {community[nb] for nb in neighbors}
            candidates.discard(current_comm)

            for target in candidates:
                gain = _modularity_gain(node, target, current_comm)
                if gain > best_gain:
                    best_gain = gain
                    best_comm = target

            if best_comm != current_comm:
                community[node] = best_comm
                improved = True

    # Relabel communities to consecutive integers
    unique = sorted(set(community))
    mapping = {old: new for new, old in enumerate(unique)}
    community = [mapping[c] for c in community]

    Q = _total_modularity(community)
    return community, Q


def _compute_clustering_and_path(adj):
    """Compute average clustering coefficient and average shortest path length."""
    n = adj.shape[0]
    binary = (adj > 0).astype(float)

    # Average clustering coefficient
    clustering = np.zeros(n)
    for i in range(n):
        neighbors = np.where(binary[i] > 0)[0]
        k = len(neighbors)
        if k < 2:
            clustering[i] = 0.0
            continue
        # Count triangles: for each pair of neighbors, check if connected
        triangles = 0
        possible = k * (k - 1) / 2.0
        for a_idx in range(k):
            for b_idx in range(a_idx + 1, k):
                a, b = neighbors[a_idx], neighbors[b_idx]
                if binary[a, b] > 0:
                    triangles += 1
        clustering[i] = (2.0 * triangles) / possible if possible > 0 else 0.0

    avg_clustering = float(clustering.mean())

    # Average shortest path length (BFS for unweighted graph)
    # Use scipy sparse for efficiency
    sparse_adj = sparse.csr_matrix(binary)
    try:
        dist_matrix = sparse.csgraph.shortest_path(sparse_adj, directed=False, unweighted=True)
        # Only consider reachable pairs (finite distances, excluding self)
        n_nodes = dist_matrix.shape[0]
        mask = np.isfinite(dist_matrix) & (dist_matrix > 0)
        if mask.sum() > 0:
            avg_path = float(dist_matrix[mask].mean())
        else:
            avg_path = 0.0
    except Exception:
        avg_path = 0.0

    return _r(avg_clustering, 4), _r(avg_path, 4)


def correlation_network(
    returns_matrix: list[list[float]],
    threshold: float = 0.3,
    asset_names: list[str] | None = None,
) -> dict:
    """Build a correlation network from asset returns.

    Args:
        returns_matrix: N assets x T days matrix of returns.
        threshold: Minimum absolute correlation to keep an edge.
        asset_names: Names of the assets.

    Returns:
        Adjacency matrix, edge list, centrality measures,
        network stats, and community detection results.
    """
    data = np.array(returns_matrix, dtype=float)
    n, t = data.shape

    if asset_names is None:
        asset_names = [f"Asset {i+1}" for i in range(n)]

    # Correlation matrix
    corr = np.corrcoef(data)
    corr = _symmetrize(corr)
    np.fill_diagonal(corr, 0.0)

    # Thresholded adjacency (absolute correlation above threshold)
    adj = np.where(np.abs(corr) >= threshold, corr, 0.0)
    adj = _symmetrize(adj)

    # Edge list
    edges = []
    for i in range(n):
        for j in range(i + 1, n):
            if adj[i, j] != 0:
                edges.append({
                    "source": asset_names[i],
                    "target": asset_names[j],
                    "weight": _r(corr[i, j]),
                })

    # Sort edges by absolute weight descending
    edges.sort(key=lambda e: abs(e["weight"]), reverse=True)

    # Centrality measures
    binary_adj = (adj != 0).astype(float)
    weighted_adj = np.abs(adj)

    # Degree centrality
    degree = binary_adj.sum(axis=1) / (n - 1) if n > 1 else np.zeros(n)

    # Betweenness centrality (on binary graph)
    betweenness = _compute_betweenness_centrality(binary_adj)

    # Eigenvector centrality (on weighted absolute graph)
    eigenvector = _compute_eigenvector_centrality(weighted_adj)

    # PageRank (on weighted absolute graph)
    pagerank = _compute_pagerank(weighted_adj)

    centrality = []
    for i in range(n):
        centrality.append({
            "asset": asset_names[i],
            "degree_centrality": _r(degree[i]),
            "betweenness_centrality": _r(betweenness[i]),
            "eigenvector_centrality": _r(eigenvector[i]),
            "pagerank": _r(pagerank[i]),
        })

    # Sort by degree centrality descending
    centrality.sort(key=lambda c: c["degree_centrality"], reverse=True)

    # Network statistics
    n_edges = len(edges)
    max_possible_edges = n * (n - 1) / 2
    density = n_edges / max_possible_edges if max_possible_edges > 0 else 0.0

    avg_clustering, avg_path = _compute_clustering_and_path(binary_adj)

    network_stats = {
        "n_nodes": n,
        "n_edges": n_edges,
        "density": _r(density, 4),
        "avg_clustering_coefficient": avg_clustering,
        "avg_path_length": avg_path,
        "threshold_used": _r(threshold, 4),
    }

    # Community detection
    communities, modularity = _louvain_community_detection(weighted_adj)
    community_groups = {}
    for i, c in enumerate(communities):
        community_groups.setdefault(c, []).append(asset_names[i])

    community_result = {
        "modularity": _r(modularity, 4),
        "n_communities": len(community_groups),
        "communities": {f"community_{k+1}": v for k, v in sorted(community_groups.items())},
    }

    return {
        "adjacency_matrix": _to_native(adj),
        "correlation_matrix": _to_native(corr),
        "edge_list": edges,
        "centrality": centrality,
        "network_stats": network_stats,
        "community_detection": community_result,
    }


# ---------------------------------------------------------------------------
# 2. Minimum Spanning Tree
# ---------------------------------------------------------------------------

def minimum_spanning_tree(
    returns_matrix: list[list[float]],
    asset_names: list[str] | None = None,
) -> dict:
    """Build MST from correlation distance matrix.

    Distance: d_ij = sqrt(2 * (1 - rho_ij))

    Args:
        returns_matrix: N assets x T days matrix of returns.
        asset_names: Names of the assets.

    Returns:
        MST edge list, adjacency matrix, and tree statistics.
    """
    data = np.array(returns_matrix, dtype=float)
    n, t = data.shape

    if asset_names is None:
        asset_names = [f"Asset {i+1}" for i in range(n)]

    # Correlation and distance matrices
    corr = np.corrcoef(data)
    corr = _symmetrize(corr)

    # Distance matrix: d_ij = sqrt(2 * (1 - rho_ij))
    dist = np.sqrt(np.clip(2.0 * (1.0 - corr), 0, None))
    np.fill_diagonal(dist, 0.0)

    # Compute MST using scipy
    sparse_dist = sparse.csr_matrix(dist)
    mst_sparse = sparse.csgraph.minimum_spanning_tree(sparse_dist)
    mst = mst_sparse.toarray()
    # scipy returns upper triangle; symmetrize
    mst = _symmetrize(mst)

    # Edge list
    edges = []
    for i in range(n):
        for j in range(i + 1, n):
            if mst[i, j] > 0:
                edges.append({
                    "source": asset_names[i],
                    "target": asset_names[j],
                    "distance": _r(mst[i, j]),
                    "correlation": _r(corr[i, j]),
                })

    edges.sort(key=lambda e: e["distance"])

    # Tree statistics
    weights = [e["distance"] for e in edges]
    total_weight = sum(weights)
    max_weight = max(weights) if weights else 0.0
    min_weight = min(weights) if weights else 0.0

    # Diameter (longest shortest path in MST)
    try:
        mst_binary = (mst > 0).astype(float)
        mst_sparse_bin = sparse.csr_matrix(mst_binary)
        path_mat = sparse.csgraph.shortest_path(mst_sparse_bin, directed=False, unweighted=True)
        finite_paths = path_mat[np.isfinite(path_mat) & (path_mat > 0)]
        diameter = int(finite_paths.max()) if finite_paths.size > 0 else 0
    except Exception:
        diameter = 0

    tree_stats = {
        "n_nodes": n,
        "n_edges": len(edges),
        "total_weight": _r(total_weight, 4),
        "max_edge_weight": _r(max_weight, 4),
        "min_edge_weight": _r(min_weight, 4),
        "avg_edge_weight": _r(total_weight / len(edges), 4) if edges else 0.0,
        "diameter": diameter,
    }

    return {
        "mst_adjacency_matrix": _to_native(mst),
        "distance_matrix": _to_native(dist),
        "edge_list": edges,
        "tree_stats": tree_stats,
    }


# ---------------------------------------------------------------------------
# 3. Contagion Simulation
# ---------------------------------------------------------------------------

def contagion_simulation(
    adjacency_matrix: list[list[float]],
    initial_shocks: dict[str, float],
    transmission_rate: float = 0.4,
    recovery_rate: float = 0.1,
    n_rounds: int = 20,
    asset_names: list[str] | None = None,
) -> dict:
    """Simulate financial contagion on a network.

    Nodes have three states: healthy (0), stressed (1), failed (2).
    Stressed nodes can recover with probability recovery_rate each round.
    Failed nodes can transmit stress to healthy neighbors with probability
    proportional to edge weight * transmission_rate.

    Args:
        adjacency_matrix: N x N weighted adjacency matrix.
        initial_shocks: Dict of {node_name: initial_loss_pct}.
        transmission_rate: Probability of stress transmission per edge per round.
        recovery_rate: Probability of recovery per round for stressed nodes.
        n_rounds: Number of simulation rounds.
        asset_names: Optional list of node names (length N).

    Returns:
        Per-round states, total system loss, contagion timeline,
        and "too big to fail" ranking.
    """
    adj = np.array(adjacency_matrix, dtype=float)
    n = adj.shape[0]

    if asset_names is None:
        asset_names = [f"Node {i}" for i in range(n)]

    name_to_idx = {name: i for i, name in enumerate(asset_names)}

    # Normalize adjacency to [0, 1] for probability calculations
    adj_abs = np.abs(adj)
    row_sums = adj_abs.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0
    adj_norm = adj_abs / row_sums

    # State: 0 = healthy, 1 = stressed, 2 = failed
    states = np.zeros(n, dtype=int)
    losses = np.zeros(n)

    # Apply initial shocks
    for name, loss_pct in initial_shocks.items():
        if name in name_to_idx:
            idx = name_to_idx[name]
            losses[idx] = loss_pct
            if loss_pct >= 50.0:
                states[idx] = 2  # failed
            elif loss_pct > 0:
                states[idx] = 1  # stressed

    # Track per-round data
    timeline = []
    state_names = {0: "healthy", 1: "stressed", 2: "failed"}

    rng = np.random.default_rng(42)

    for round_num in range(n_rounds):
        round_data = {
            "round": round_num + 1,
            "node_states": [
                {
                    "node": asset_names[i],
                    "state": state_names[int(states[i])],
                    "loss_pct": _r(losses[i]),
                }
                for i in range(n)
            ],
            "n_healthy": int(np.sum(states == 0)),
            "n_stressed": int(np.sum(states == 1)),
            "n_failed": int(np.sum(states == 2)),
            "total_system_loss_pct": _r(losses.mean()),
        }
        timeline.append(round_data)

        # Stop if no stressed or failed nodes
        if np.sum(states > 0) == 0:
            break

        # Transmission: stressed/failed nodes transmit to healthy neighbors
        new_states = states.copy()
        new_losses = losses.copy()

        for i in range(n):
            if states[i] == 0:
                continue  # healthy nodes don't transmit

            neighbors = np.where(adj_norm[i] > 0)[0]
            for j in neighbors:
                if states[j] != 0:
                    continue  # only affect healthy nodes

                # Transmission probability = edge_weight * transmission_rate
                prob = float(adj_norm[i, j]) * transmission_rate
                # Failed nodes transmit more aggressively
                if states[i] == 2:
                    prob *= 1.5

                if rng.random() < prob:
                    # Stress transmitted
                    new_states[j] = 1
                    # Loss propagates: proportional to source loss * edge weight
                    transmitted_loss = losses[i] * float(adj_norm[i, j]) * 0.3
                    new_losses[j] = min(losses[j] + transmitted_loss, 100.0)

                    # Check if new loss pushes to failed
                    if new_losses[j] >= 50.0:
                        new_states[j] = 2

        # Recovery: stressed nodes may recover
        for i in range(n):
            if states[i] == 1 and rng.random() < recovery_rate:
                new_states[i] = 0
                new_losses[i] *= 0.8  # partial recovery of losses

        states = new_states
        losses = new_losses

    # Summary
    final_healthy = int(np.sum(states == 0))
    final_stressed = int(np.sum(states == 1))
    final_failed = int(np.sum(states == 2))
    total_loss = _r(losses.mean())

    # "Too Big to Fail" ranking: shock each node individually and count cascading failures
    tbf_ranking = []
    for node_idx in range(n):
        test_states = np.zeros(n, dtype=int)
        test_losses = np.zeros(n)
        test_states[node_idx] = 2
        test_losses[node_idx] = 60.0

        rng_tbtf = np.random.default_rng(node_idx)
        for _ in range(n_rounds):
            new_ts = test_states.copy()
            new_tl = test_losses.copy()

            for i in range(n):
                if test_states[i] == 0:
                    continue
                neighbors = np.where(adj_norm[i] > 0)[0]
                for j in neighbors:
                    if test_states[j] != 0:
                        continue
                    prob = float(adj_norm[i, j]) * transmission_rate
                    if test_states[i] == 2:
                        prob *= 1.5
                    if rng_tbtf.random() < prob:
                        new_ts[j] = 1
                        transmitted_loss = test_losses[i] * float(adj_norm[i, j]) * 0.3
                        new_tl[j] = min(test_losses[j] + transmitted_loss, 100.0)
                        if new_tl[j] >= 50.0:
                            new_ts[j] = 2

            for i in range(n):
                if test_states[i] == 1 and rng_tbtf.random() < recovery_rate:
                    new_ts[i] = 0
                    new_tl[i] *= 0.8

            test_states = new_ts
            test_losses = new_tl

        n_failed_cascade = int(np.sum(test_states == 2)) - 1  # exclude initial
        n_stressed_cascade = int(np.sum(test_states == 1))
        total_cascade_loss = _r(test_losses.mean())

        tbf_ranking.append({
            "node": asset_names[node_idx],
            "cascading_failures": max(n_failed_cascade, 0),
            "cascading_stressed": n_stressed_cascade,
            "avg_system_loss_pct": total_cascade_loss,
            "systemic_impact_score": _r(
                n_failed_cascade * 2.0 + n_stressed_cascade * 0.5 + total_cascade_loss * 0.1
            ),
        })

    tbf_ranking.sort(key=lambda x: x["systemic_impact_score"], reverse=True)

    return {
        "contagion_timeline": timeline,
        "summary": {
            "n_rounds_simulated": len(timeline),
            "final_n_healthy": final_healthy,
            "final_n_stressed": final_stressed,
            "final_n_failed": final_failed,
            "total_system_loss_pct": total_loss,
            "transmission_rate": _r(transmission_rate),
            "recovery_rate": _r(recovery_rate),
        },
        "too_big_to_fail_ranking": tbf_ranking,
    }


# ---------------------------------------------------------------------------
# 4. Systemic Risk Metrics
# ---------------------------------------------------------------------------

def systemic_risk_metrics(
    returns_matrix: list[list[float]],
    asset_names: list[str] | None = None,
    confidence_level: float = 0.95,
) -> dict:
    """Compute systemic risk indicators.

    Metrics:
    - CoVaR (Conditional Value at Risk)
    - SRISK (Simplified Brownlees & Engle systemic risk score)
    - MES (Marginal Expected Shortfall)
    - Diebold-Yilmann connectedness index

    Args:
        returns_matrix: N assets x T days matrix of returns.
        asset_names: Names of the assets.
        confidence_level: VaR confidence level (default 0.95).

    Returns:
        Per-asset risk scores and systemic rankings.
    """
    data = np.array(returns_matrix, dtype=float)
    n, t = data.shape

    if asset_names is None:
        asset_names = [f"Asset {i+1}" for i in range(n)]

    alpha = 1.0 - confidence_level
    var_quantile = stats.norm.ppf(alpha)  # negative value

    # -----------------------------------------------------------------------
    # VaR and ES for each asset
    # -----------------------------------------------------------------------
    means = data.mean(axis=1)
    stds = data.std(axis=1, ddof=1)
    stds[stds < 1e-10] = 1e-10

    # Parametric VaR (return is negative = loss)
    var_values = means + var_quantile * stds

    # Historical VaR
    hist_var = np.percentile(data, alpha * 100, axis=1)

    # Expected Shortfall (average of returns below VaR)
    es_values = np.zeros(n)
    for i in range(n):
        below_var = data[i, data[i] <= hist_var[i]]
        es_values[i] = below_var.mean() if len(below_var) > 0 else hist_var[i]

    # -----------------------------------------------------------------------
    # CoVaR: Conditional VaR of asset i given asset j is in distress
    # -----------------------------------------------------------------------
    # For each pair (i, j), compute quantile regression approximation
    # Simplified: CoVaR_{i|j} = E[R_i | R_j <= VaR_j]
    covar_matrix = np.zeros((n, n))
    for j in range(n):
        distress_mask = data[j] <= hist_var[j]
        if distress_mask.sum() < 5:
            # Not enough distress observations; use correlation-based estimate
            corr_row = np.corrcoef(data)[j]
            for i in range(n):
                covar_matrix[i, j] = means[i] + var_quantile * stds[i] * abs(corr_row[i]) * 1.2
        else:
            for i in range(n):
                covar_matrix[i, j] = data[i, distress_mask].mean()

    # Delta CoVaR: CoVaR - VaR (incremental contribution)
    delta_covar = covar_matrix - var_values[:, np.newaxis]

    # -----------------------------------------------------------------------
    # MES: Marginal Expected Shortfall
    # MES_i = E[R_i | R_market <= VaR_market]
    # Use equal-weighted market proxy
    # -----------------------------------------------------------------------
    market_returns = data.mean(axis=0)  # equal-weighted market
    market_var = np.percentile(market_returns, alpha * 100)
    market_distress = market_returns <= market_var

    mes_values = np.zeros(n)
    for i in range(n):
        if market_distress.sum() > 0:
            mes_values[i] = data[i, market_distress].mean()
        else:
            mes_values[i] = es_values[i]

    # -----------------------------------------------------------------------
    # SRISK (Simplified Brownlees & Engle, 2017)
    # SRISK_i = E[Loss_i | Crisis] - k * (Debt_i / Equity_i)
    # Simplification: Use volatility and downside correlation as proxies
    # SRISK_i = LRMES_i * (1 - LTV) * Size_i
    # where LRMES is approximated using MES
    # -----------------------------------------------------------------------
    # Simplified SRISK using: size proxy (inverse of avg return), leverage proxy
    # (skewness of returns), and LRMES from MES
    lrmes = np.exp(mes_values * (-22.0 / 252.0))  # annualized long-run MES
    lrmes = np.clip(lrmes, 0, 2)

    # Size proxy: use mean absolute return as relative size indicator
    size_proxy = np.abs(means) / (np.abs(means).mean() + 1e-10)

    # Leverage proxy: use negative skewness as a proxy for leverage
    skewness = np.zeros(n)
    for i in range(n):
        m = means[i]
        s = stds[i]
        if s > 1e-10:
            skewness[i] = np.mean(((data[i] - m) / s) ** 3)

    leverage_proxy = np.clip(1.0 - 0.5 * skewness, 0.5, 3.0)

    # Simplified SRISK score (normalized)
    k = 0.08  # 8% capital requirement
    srisk_raw = lrmes * leverage_proxy * size_proxy - k * leverage_proxy
    srisk_raw = np.clip(srisk_raw, 0, None)
    srisk_total = srisk_raw.sum()
    srisk_pct = srisk_raw / srisk_total if srisk_total > 0 else np.ones(n) / n

    # -----------------------------------------------------------------------
    # Diebold-Yilmann Connectedness Index
    # -----------------------------------------------------------------------
    # Use variance decomposition based on correlation structure
    # Simplified approach: FEVD from Cholesky decomposition of correlation
    corr = np.corrcoef(data)
    corr = _symmetrize(corr)

    try:
        L = np.linalg.cholesky(corr)
        # Variance decomposition: each asset's variance explained by others
        L_sq = L ** 2
        row_sums = L_sq.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0
        fevd = L_sq / row_sums

        # Connectedness table
        # TO (how much i transmits to others)
        to_others = np.zeros(n)
        # FROM (how much i receives from others)
        from_others = np.zeros(n)
        for i in range(n):
            for j in range(n):
                if i != j:
                    to_others[i] += fevd[j, i]  # i's contribution to j
                    from_others[i] += fevd[i, j]  # j's contribution to i

        total_connectedness = to_others.sum() / n * 100  # percentage

        # Net directional connectedness
        net_connectedness = to_others - from_others
    except np.linalg.LinAlgError:
        # Fallback: use absolute correlation sums
        to_others = np.sum(np.abs(corr), axis=0) - 1.0
        from_others = np.sum(np.abs(corr), axis=1) - 1.0
        total_connectedness = _r(to_others.mean() / (n - 1) * 100) if n > 1 else 0.0
        net_connectedness = to_others - from_others
        fevd = np.abs(corr)

    # -----------------------------------------------------------------------
    # Aggregate results
    # -----------------------------------------------------------------------
    per_asset = []
    for i in range(n):
        per_asset.append({
            "asset": asset_names[i],
            "mean_return": _r(means[i]),
            "volatility": _r(stds[i]),
            "parametric_var": _r(var_values[i]),
            "historical_var": _r(hist_var[i]),
            "expected_shortfall": _r(es_values[i]),
            "mes": _r(mes_values[i]),
            "lrmes": _r(lrmes[i]),
            "srisk_score": _r(srisk_raw[i]),
            "srisk_contribution_pct": _r(srisk_pct[i] * 100, 2),
            "delta_covar_avg": _r(delta_covar[i].mean()),
            "delta_covar_received_max": _r(delta_covar[i].max()),
            "connectedness_to_others": _r(to_others[i]),
            "connectedness_from_others": _r(from_others[i]),
            "net_connectedness": _r(net_connectedness[i]),
        })

    # Systemic rankings
    # 1. By SRISK
    srisk_ranking = sorted(per_asset, key=lambda x: x["srisk_score"], reverse=True)
    # 2. By MES (most negative = most systemic)
    mes_ranking = sorted(per_asset, key=lambda x: x["mes"])
    # 3. By net connectedness
    conn_ranking = sorted(per_asset, key=lambda x: x["net_connectedness"], reverse=True)
    # 4. By CoVaR (average delta CoVaR received)
    covar_ranking = sorted(per_asset, key=lambda x: x["delta_covar_avg"])

    return {
        "confidence_level": confidence_level,
        "n_assets": n,
        "n_observations": t,
        "per_asset_risk": per_asset,
        "systemic_rankings": {
            "by_srisk": [{"rank": i+1, "asset": x["asset"], "srisk_score": x["srisk_score"]} for i, x in enumerate(srisk_ranking)],
            "by_mes": [{"rank": i+1, "asset": x["asset"], "mes": x["mes"]} for i, x in enumerate(mes_ranking)],
            "by_connectedness": [{"rank": i+1, "asset": x["asset"], "net_connectedness": x["net_connectedness"]} for i, x in enumerate(conn_ranking)],
            "by_delta_covar": [{"rank": i+1, "asset": x["asset"], "delta_covar_avg": x["delta_covar_avg"]} for i, x in enumerate(covar_ranking)],
        },
        "connectedness_table": _to_native(fevd),
        "total_connectedness_index": _r(total_connectedness, 2),
        "market_var": _r(market_var),
        "n_crisis_days": int(market_distress.sum()),
    }


# ---------------------------------------------------------------------------
# 5. Demo
# ---------------------------------------------------------------------------

def network_analysis_demo() -> dict:
    """Demo with 12 TSE stocks across 5 sectors.

    Sectors:
        - Banking: Mellat, Melli, Saderat, Tejarat
        - Petrochemical: Persian Gulf, Tabriz, Shiraz
        - Steel: Mobarakeh, Esfahan, Khouzestan
        - Automotive: Iran Khodro, Saipa
        - Telecom: Mobile Communication

    Generates 504 days of correlated returns and runs all analyses.
    """
    np.random.seed(42)

    sectors = {
        "Banking": ["Mellat", "Melli", "Saderat"],
        "Petrochemical": ["Persian Gulf", "Tabriz Refinery", "Shiraz Petrochem"],
        "Steel": ["Mobarakeh", "Esfahan Steel", "Khouzestan Steel"],
        "Automotive": ["Iran Khodro", "Saipa"],
        "Telecom": ["Mobile Communication"],
    }

    asset_names = []
    sector_map = {}
    for sector, stocks in sectors.items():
        for stock in stocks:
            asset_names.append(stock)
            sector_map[stock] = sector

    n = len(asset_names)  # 12
    t = 504
    n_sectors = len(sectors)

    # Sector-level parameters
    sector_names = list(sectors.keys())
    sector_means = np.array([0.0004, 0.0003, 0.0005, 0.0002, 0.0006])
    sector_vols = np.array([0.018, 0.022, 0.020, 0.025, 0.015])

    # Sector factor returns
    factor_returns = np.zeros((n_sectors, t))
    for s in range(n_sectors):
        factor_returns[s] = np.random.normal(sector_means[s], sector_vols[s], t)

    # Add sector correlation (banking and petrochemical somewhat correlated)
    sector_corr = np.array([
        [1.0, 0.4, 0.3, 0.2, 0.1],
        [0.4, 1.0, 0.5, 0.15, 0.1],
        [0.3, 0.5, 1.0, 0.25, 0.05],
        [0.2, 0.15, 0.25, 1.0, 0.2],
        [0.1, 0.1, 0.05, 0.2, 1.0],
    ])

    # Apply sector correlation via Cholesky
    L_sector = np.linalg.cholesky(sector_corr)
    correlated_factors = L_sector @ factor_returns

    # Generate individual stock returns
    # idiosyncratic volatility
    idio_vols = {
        "Mellat": 0.008, "Melli": 0.010, "Saderat": 0.012,
        "Persian Gulf": 0.009, "Tabriz Refinery": 0.011, "Shiraz Petrochem": 0.010,
        "Mobarakeh": 0.007, "Esfahan Steel": 0.012, "Khouzestan Steel": 0.013,
        "Iran Khodro": 0.015, "Saipa": 0.016,
        "Mobile Communication": 0.008,
    }

    # Factor loadings (beta to sector factor)
    factor_betas = {
        "Mellat": 0.9, "Melli": 0.85, "Saderat": 1.1,
        "Persian Gulf": 1.0, "Tabriz Refinery": 0.8, "Shiraz Petrochem": 0.9,
        "Mobarakeh": 1.05, "Esfahan Steel": 0.75, "Khouzestan Steel": 0.85,
        "Iran Khodro": 1.2, "Saipa": 1.15,
        "Mobile Communication": 0.7,
    }

    returns = np.zeros((n, t))
    for i, name in enumerate(asset_names):
        sector_idx = sector_names.index(sector_map[name])
        beta = factor_betas[name]
        idio_vol = idio_vols[name]
        idio = np.random.normal(0, idio_vol, t)
        returns[i] = beta * correlated_factors[sector_idx] + idio

    # Run all analyses
    corr_net = correlation_network(returns.tolist(), threshold=0.3, asset_names=asset_names)
    mst = minimum_spanning_tree(returns.tolist(), asset_names=asset_names)

    # For contagion, use the correlation-based adjacency
    adj_for_contagion = np.array(corr_net["adjacency_matrix"])
    # Take absolute values and normalize for contagion
    adj_abs = np.abs(adj_for_contagion)
    row_sums = adj_abs.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0
    adj_normalized = adj_abs / row_sums

    initial_shocks = {
        "Mellat": 55.0,
        "Persian Gulf": 45.0,
    }
    contagion = contagion_simulation(
        adj_normalized.tolist(),
        initial_shocks,
        transmission_rate=0.35,
        recovery_rate=0.08,
        n_rounds=15,
        asset_names=asset_names,
    )

    risk = systemic_risk_metrics(returns.tolist(), asset_names=asset_names)

    return {
        "demo_info": {
            "title": "TSE Network Analysis Demo",
            "n_assets": n,
            "n_days": t,
            "sectors": sectors,
            "sector_map": sector_map,
        },
        "correlation_network": {
            "network_stats": corr_net["network_stats"],
            "community_detection": corr_net["community_detection"],
            "top_edges": corr_net["edge_list"][:10],
            "centrality_top5": corr_net["centrality"][:5],
        },
        "minimum_spanning_tree": {
            "tree_stats": mst["tree_stats"],
            "edge_list": mst["edge_list"],
        },
        "contagion_simulation": {
            "summary": contagion["summary"],
            "too_big_to_fail_top5": contagion["too_big_to_fail_ranking"][:5],
            "timeline_summary": [
                {
                    "round": r["round"],
                    "n_healthy": r["n_healthy"],
                    "n_stressed": r["n_stressed"],
                    "n_failed": r["n_failed"],
                    "total_system_loss_pct": r["total_system_loss_pct"],
                }
                for r in contagion["contagion_timeline"]
            ],
        },
        "systemic_risk": {
            "total_connectedness_index": risk["total_connectedness_index"],
            "n_crisis_days": risk["n_crisis_days"],
            "market_var": risk["market_var"],
            "top_srisk": risk["systemic_rankings"]["by_srisk"][:5],
            "top_mes": risk["systemic_rankings"]["by_mes"][:5],
            "top_connectedness": risk["systemic_rankings"]["by_connectedness"][:5],
            "per_asset_summary": [
                {
                    "asset": a["asset"],
                    "sector": sector_map[a["asset"]],
                    "volatility": a["volatility"],
                    "historical_var": a["historical_var"],
                    "mes": a["mes"],
                    "srisk_score": a["srisk_score"],
                    "net_connectedness": a["net_connectedness"],
                }
                for a in risk["per_asset_risk"]
            ],
        },
    }
