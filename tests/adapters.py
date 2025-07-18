from __future__ import annotations

import os
from typing import IO, Any, BinaryIO
from collections.abc import Iterable
from jaxtyping import Float, Int

import numpy.typing as npt
import torch
from torch import Tensor



def run_linear(
    d_in: int,
    d_out: int,
    weights: Float[Tensor, " d_out d_in"],
    in_features: Float[Tensor, " ... d_in"],
) -> Float[Tensor, " ... d_out"]:
    """
    Given the weights of a Linear layer, compute the transformation of a batched input.

    Args:
        in_dim (int): The size of the input dimension
        out_dim (int): The size of the output dimension
        weights (Float[Tensor, "d_out d_in"]): The linear weights to use
        in_features (Float[Tensor, "... d_in"]): The output tensor to apply the function to
    
    Returns:
        Float[Tensor, "... d_out"]: The transformed output of your linear module.
    """
    import torch
    from torch import nn

    class Linear(nn.Module):
        def __init__(self, in_features, out_features, device=None, dtype=None):
            super.__init__()

            self.W = nn.Parameter(torch.empty((out_features, in_features), device=device, dtype=dtype))
            torch.nn.init.trunc_normal_(self.W.data, a=-3.0, b=3.0)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
             return torch.einsum('bi, oi -> bi', x, self.W)

    raise NotImplementedError


def run_embedding(
    vocab_size: int,
    d_model: int,
    weights: Float[Tensor, " vocab_size d_model"],
    token_ids: Int[Tensor, " ..."],
) -> Float[Tensor, " ... d_model"]:
    """
    Given the weights of an Embedding layer, get the embeddings for a batch of token ids.

    Args:
        vocab_size (int): The number of embeddings in the vocabulary
        d_model (int): The size of the embedding dimension
        weights (Float[Tensor, "vocab_size d_model"]): The embedding vectors to fetch from
        token_ids (Int[Tensor, "..."]): The set of token ids to fetch from the Embedding layer
    
    Returns:
        Float[Tensor, "... d_model"]: Batch of embeddings returned by your Embedding layer.
    """
    import torch
    from torch import nn

    class Embedding(nn.Module):
        def __init__(self, num_embeddings, embedding_dim, device=None, dtype=None):
            super().__init__()

            self.embedding = nn.Parameter(torch.empty((num_embeddings, embedding_dim), device=device, dtype=dtype))

            torch.nn.init.trunc_normal_(self.W.data, a=-3.0, b=3.0)

        def forward(self, token_ids: torch.Tensor) -> torch.Tensor:
            return self.embedding[token_ids]

    raise NotImplementedError


def run_swiglu(
    d_model: int,
    d_ff: int,
    w1_weight: Float[Tensor, " d_ff d_model"],
    w2_weight: Float[Tensor, " d_model d_ff"],
    w3_weight: Float[Tensor, " d_ff d_model"],
    in_features: Float[Tensor, " ... d_model"],
) -> Float[Tensor, " ... d_model"]:
    """Given the weights of a SwiGLU network, return
    the output of your implementation with these weights.

    Args:
        d_model (int): Dimensionality of the feedforward input and output.
        d_ff (int): Dimensionality of the up-project happening internally to your swiglu.
        w1_weight (Float[Tensor, "d_ff d_model"]): Stored weights for W1
        w2_weight (Float[Tensor, "d_model d_ff"]): Stored weights for W2
        w3_weight (Float[Tensor, "d_ff d_model"]): Stored weights for W3
        in_features (Float[Tensor, "... d_model"]): Input embeddings to the feed-forward layer.

    Returns:
        Float[Tensor, "... d_model"]: Output embeddings of the same shape as the input embeddings.
    """
    # Example:
    # If your state dict keys match, you can use `load_state_dict()`
    # swiglu.load_state_dict(weights)
    # You can also manually assign the weights
    # swiglu.w1.weight.data = w1_weight
    # swiglu.w2.weight.data = w2_weight
    # swiglu.w3.weight.data = w3_weight
    import torch
    from torch import nn
    import math

    class SwiGLUFeedForward(nn.Module):
        def __init__(self, d_model: int, device=None, dtype=None):
            super.__init__()

            d_ff_raw = d_model * 8 / 3

            d_ff = int(math.ceil(d_ff_raw / 64) * 64)

            self.w1 = nn.Parameter(torch.empty(d_model, 2 * d_ff, device=device, dtype=dtype))
            self.b1 = nn.Parameter(torch.zero(2 * d_ff, device=device, dtype=dtype))

            self.w2 = nn.Parameter(torch.empty(d_ff, d_model, device=device, dtype=dtype))
            self.b2 = nn.Parameter(torch.zeros(d_model, device=device, dtype=dtype))

            nn.init.trunc_normal_(self.w1)
            nn.init.trunc_normal_(self.w2)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            x_proj = torch.einsum("bsd, dk -> bsk", x, self.w1) + self.b1

            value, gate = x_proj.chunk(2, dim=1)

            x_act = value * torch.nn.functional.relu(gate)

            out = torch.einsum("bsd, dk -> bsk", x_act, self.w2) + self.b2
            return out

    raise NotImplementedError


def run_scaled_dot_product_attention(
    Q: Float[Tensor, " ... queries d_k"],
    K: Float[Tensor, " ... keys d_k"],
    V: Float[Tensor, " ... values d_v"],
    mask: Float[Tensor, " ... queries keys"] | None = None,
) -> Float[Tensor, " ... queries d_v"]:
    """
    Given key (K), query (Q), and value (V) tensors, return
    the output of your scaled dot product attention implementation.

    Args:
        Q (Float[Tensor, " ... queries d_k"]): Query tensor
        K (Float[Tensor, " ... keys d_k"]): Key tensor
        V (Float[Tensor, " ... values d_v"]): Values tensor
        mask (Float[Tensor, " ... queries keys"] | None): Mask tensor
    Returns:
        Float[Tensor, " ... queries d_v"]: Output of SDPA
    """
    import torch
    from torch import nn
    import math

    def softmax(x: torch.Tensor, dim: int) -> torch.Tensor:
        x_max = torch.amax(x, dim, keepdim=True)
        x_stable = x - x_max

        exp_x = torch.exp(x_stable)
        sum_exp = torch.sum(exp_x, dim, keepdim=True)

        return exp_x / sum_exp

    def scaled_dot_product_attention(q, k, v, mask=None):
        """
        :param q: (..., seq_len_q, d_k)
        :param k: (..., seq_len_k, d_k)
        :param v: (..., seq_len_v, d_v)
        :param mask: optional (..., seq_len_q, seq_len_k) of bool
        :return: output (..., seq_len_q, d_v)
        """

        d_k = q.size(-1)

        scores = torch.einsum('...ik, ...jk -> ...ij', q, k) / math.sqrt(d_k)

        if mask is not None:
            scores = scores.masked_fill(~mask, float('-inf'))

        attn_weights = softmax(scores, dim=-1)

        output = torch.einsum('...ik, ...jk -> ...ij', attn_weights, v)

        return output
    raise NotImplementedError


def run_multihead_self_attention(
    d_model: int,
    num_heads: int,
    q_proj_weight: Float[Tensor, " d_k d_in"],
    k_proj_weight: Float[Tensor, " d_k d_in"],
    v_proj_weight: Float[Tensor, " d_v d_in"],
    o_proj_weight: Float[Tensor, " d_model d_v"],
    in_features: Float[Tensor, " ... sequence_length d_in"],
) -> Float[Tensor, " ... sequence_length d_out"]:
    """
    Given the key, query, and value projection weights of a naive unbatched
    implementation of multi-head attention, return the output of an optimized batched
    implementation. This implementation should handle the key, query, and value projections
    for all heads in a single matrix multiply.
    This function should not use RoPE.
    See section 3.2.2 of Vaswani et al., 2017.

    Args:
        d_model (int): Dimensionality of the feedforward input and output.
        num_heads (int): Number of heads to use in multi-headed attention.
        max_seq_len (int): Maximum sequence length to pre-cache if your implementation does that.
        q_proj_weight (Float[Tensor, "d_k d_in"]): Weights for the Q projection
        k_proj_weight (Float[Tensor, "d_k d_in"]): Weights for the K projection
        v_proj_weight (Float[Tensor, "d_k d_in"]): Weights for the V projection
        o_proj_weight (Float[Tensor, "d_model d_v"]): Weights for the output projection
        in_features (Float[Tensor, "... sequence_length d_in"]): Tensor to run your implementation on.

    Returns:
        Float[Tensor, " ... sequence_length d_out"]: Tensor with the output of running your optimized, batched multi-headed attention
        implementation with the given QKV projection weights and input features.
    """
    import torch
    from torch import nn
    import math

    def softmax(x: torch.Tensor, dim: int) -> torch.Tensor:
        x_max = torch.amax(x, dim, keepdim=True)
        x_stable = x - x_max

        exp_x = torch.exp(x_stable)
        sum_exp = torch.sum(exp_x, dim, keepdim=True)

        return exp_x / sum_exp

    class Linear(nn.Module):
        def __init__(self, in_features, out_features, device=None, dtype=None):
            super.__init__()

            self.W = nn.Parameter(
                torch.empty((out_features, in_features), device=device, dtype=dtype))
            torch.nn.init.trunc_normal_(self.W.data, a=-3.0, b=3.0)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return torch.einsum('bi, oi -> bi', x, self.W)

    def scaled_dot_product_attention(q, k, v, mask=None):
        """
        :param q: (..., seq_len_q, d_k)
        :param k: (..., seq_len_k, d_k)
        :param v: (..., seq_len_v, d_v)
        :param mask: optional (..., seq_len_q, seq_len_k) of bool
        :return: output (..., seq_len_q, d_v)
        """

        d_k = q.size(-1)

        scores = torch.einsum('...ik, ...jk -> ...ij', q, k) / math.sqrt(d_k)

        if mask is not None:
            scores = scores.masked_fill(~mask, float('-inf'))

        attn_weights = softmax(scores, dim=-1)

        output = torch.einsum('...ik, ...jk -> ...ij', attn_weights, v)

        return output

    class MultiHeadSelfAttention(nn.Module):
        def __init__(self, d_model: int, num_heads: int, rope: nn.Module):
            super.__init__()
            assert d_model % num_heads == 0

            self.d_model = d_model
            self.num_heads = num_heads
            self.d_k = d_model // num_heads
            self.d_v = self.d_k

            self.q_proj = Linear(d_model, d_model)
            self.k_proj = Linear(d_model, d_model)
            self.v_proj = Linear(d_model, d_model)
            self.out_proj = Linear(d_model, d_model)

            self.rope = rope

        def forward(self, x: torch.Tensor, token_positions: torch.Tensor) -> torch.Tensor:
            batch_size, seq_len, _ = x.shape

            q = self.q_proj(x)
            k = self.k_proj(x)
            v = self.v_proj(x)

            # Reshape: (batch_size, seq_len, num_heads, d_k) -> (batch, num_heads, seq_len, d_k)
            def split_heads(t):
                return t.view(batch_size, seq_len, self.num_heads, self.d_k).transpose(1, 2)

            q = split_heads(q)
            k = split_heads(k)
            v = split_heads(v)

            # Apply RoPE
            q = self.rope(q, token_positions)
            k = self.rope(k, token_positions)

            # Create casual mask
            casual_mask = torch.triu(torch.ones(seq_len, seq_len))

            # Compute scaled dot-product attention
            attn_output = scaled_dot_product_attention(q, k, v, mask=casual_mask)

            # Merge_heads: (batch, num_heads, seq_len, d_k) -> (batch, seq_len, d_k)
            attn_output = torch.einsum('bnld-> bld', attn_output).reshape(batch_size, seq_len, self.d_model)

            return self.out_proj(attn_output)

    raise NotImplementedError


def run_multihead_self_attention_with_rope(
    d_model: int,
    num_heads: int,
    max_seq_len: int,
    theta: float,
    q_proj_weight: Float[Tensor, " d_k d_in"],
    k_proj_weight: Float[Tensor, " d_k d_in"],
    v_proj_weight: Float[Tensor, " d_v d_in"],
    o_proj_weight: Float[Tensor, " d_model d_v"],
    in_features: Float[Tensor, " ... sequence_length d_in"],
    token_positions: Int[Tensor, " ... sequence_length"] | None = None,
) -> Float[Tensor, " ... sequence_length d_out"]:
    """
    Given the key, query, and value projection weights of a naive unbatched
    implementation of multi-head attention, return the output of an optimized batched
    implementation. This implementation should handle the key, query, and value projections
    for all heads in a single matrix multiply.
    This version of MHA should include RoPE.
    In this case, the RoPE embedding dimension must be the head embedding dimension (d_model // num_heads).
    See section 3.2.2 of Vaswani et al., 2017.

    Args:
        d_model (int): Dimensionality of the feedforward input and output.
        num_heads (int): Number of heads to use in multi-headed attention.
        max_seq_len (int): Maximum sequence length to pre-cache if your implementation does that.
        theta (float): RoPE parameter.
        q_proj_weight (Float[Tensor, "d_k d_in"]): Weights for the Q projection
        k_proj_weight (Float[Tensor, "d_k d_in"]): Weights for the K projection
        v_proj_weight (Float[Tensor, "d_k d_in"]): Weights for the V projection
        o_proj_weight (Float[Tensor, "d_model d_v"]): Weights for the output projection
        in_features (Float[Tensor, "... sequence_length d_in"]): Tensor to run your implementation on.
        token_positions (Int[Tensor, " ... sequence_length"] | None): Optional tensor with the positions of the tokens

    Returns:
        Float[Tensor, " ... sequence_length d_out"]: Tensor with the output of running your optimized, batched multi-headed attention
        implementation with the given QKV projection weights and input features.
    """
    raise NotImplementedError


def run_rope(
    d_k: int,
    theta: float,
    max_seq_len: int,
    in_query_or_key: Float[Tensor, " ... sequence_length d_k"],
    token_positions: Int[Tensor, " ... sequence_length"],
) -> Float[Tensor, " ... sequence_length d_k"]:
    """
    Run RoPE for a given input tensor.

    Args:
        d_k (int): Embedding dimension size for the query or key tensor.
        theta (float): RoPE parameter.
        max_seq_len (int): Maximum sequence length to pre-cache if your implementation does that.
        in_query_or_key (Float[Tensor, "... sequence_length d_k"]): Input tensor to run RoPE on.
        token_positions (Int[Tensor, "... sequence_length"]): Tensor of shape (batch_size, sequence_length) with the token positions
    Returns:
        Float[Tensor, " ... sequence_length d_k"]: Tensor with RoPEd input.
    """
    raise NotImplementedError


def run_transformer_block(
    d_model: int,
    num_heads: int,
    d_ff: int,
    max_seq_len: int,
    theta: float,
    weights: dict[str, Tensor],
    in_features: Float[Tensor, " batch sequence_length d_model"],
) -> Float[Tensor, " batch sequence_length d_model"]:
    """
    Given the weights of a pre-norm Transformer block and input features,
    return the output of running the Transformer block on the input features.

    This function should use RoPE.
    Depending on your implementation, you may simply need to pass the relevant args
    to your TransformerBlock constructor, or you may need to initialize your own RoPE
    class and pass that instead.

    Args:
        d_model (int): The dimensionality of the Transformer block input.
        num_heads (int): Number of heads to use in multi-headed attention. `d_model` must be
            evenly divisible by `num_heads`.
        d_ff (int): Dimensionality of the feed-forward inner layer.
        max_seq_len (int): Maximum sequence length to pre-cache if your implementation does that.
        theta (float): RoPE parameter.
        weights (dict[str, Tensor]):
            State dict of our reference implementation.
            The keys of this dictionary are:
            - `attn.q_proj.weight`
                The query projections for all `num_heads` attention heads.
                Shape is (d_model, d_model).
                The rows are ordered by matrices of shape (num_heads, d_k),
                so `attn.q_proj.weight == torch.cat([q_heads.0.weight, ..., q_heads.N.weight], dim=0)`.
            - `attn.k_proj.weight`
                The key projections for all `num_heads` attention heads.
                Shape is (d_model, d_model).
                The rows are ordered by matrices of shape (num_heads, d_k),
                so `attn.k_proj.weight == torch.cat([k_heads.0.weight, ..., k_heads.N.weight], dim=0)`.
            - `attn.v_proj.weight`
                The value projections for all `num_heads` attention heads.
                Shape is (d_model, d_model).
                The rows are ordered by matrices of shape (num_heads, d_v),
                so `attn.v_proj.weight == torch.cat([v_heads.0.weight, ..., v_heads.N.weight], dim=0)`.
            - `attn.output_proj.weight`
                Weight of the multi-head self-attention output projection
                Shape is (d_model, d_model).
            - `ln1.weight`
                Weights of affine transform for the first RMSNorm
                applied in the transformer block.
                Shape is (d_model,).
            - `ffn.w1.weight`
                Weight of the first linear transformation in the FFN.
                Shape is (d_model, d_ff).
            - `ffn.w2.weight`
                Weight of the second linear transformation in the FFN.
                Shape is (d_ff, d_model).
            - `ffn.w3.weight`
                Weight of the third linear transformation in the FFN.
                Shape is (d_model, d_ff).
            - `ln2.weight`
                Weights of affine transform for the second RMSNorm
                applied in the transformer block.
                Shape is (d_model,).
        in_features (Float[Tensor, "batch sequence_length d_model"]):
            Tensor to run your implementation on.

    Returns:
        Float[Tensor, "batch sequence_length d_model"] Tensor with the output of
        running the Transformer block on the input features while using RoPE.
    """
    import torch
    from torch import nn, optim
    import math

    # Multi head self attention
    def softmax(x: torch.Tensor, dim: int) -> torch.Tensor:
        x_max = torch.amax(x, dim, keepdim=True)
        x_stable = x - x_max

        exp_x = torch.exp(x_stable)
        sum_exp = torch.sum(exp_x, dim, keepdim=True)

        return exp_x / sum_exp

    class Linear(nn.Module):
        def __init__(self, in_features, out_features, device=None, dtype=None):
            super.__init__()

            self.W = nn.Parameter(
                torch.empty((out_features, in_features), device=device, dtype=dtype))
            torch.nn.init.trunc_normal_(self.W.data, a=-3.0, b=3.0)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return torch.einsum('bi, oi -> bi', x, self.W)

    def scaled_dot_product_attention(q, k, v, mask=None):
        """
        :param q: (..., seq_len_q, d_k)
        :param k: (..., seq_len_k, d_k)
        :param v: (..., seq_len_v, d_v)
        :param mask: optional (..., seq_len_q, seq_len_k) of bool
        :return: output (..., seq_len_q, d_v)
        """

        d_k = q.size(-1)

        scores = torch.einsum('...ik, ...jk -> ...ij', q, k) / math.sqrt(d_k)

        if mask is not None:
            scores = scores.masked_fill(~mask, float('-inf'))

        attn_weights = softmax(scores, dim=-1)

        output = torch.einsum('...ik, ...jk -> ...ij', attn_weights, v)

        return output

    class MultiHeadSelfAttention(nn.Module):
        def __init__(self, d_model: int, num_heads: int, rope: nn.Module):
            super.__init__()
            assert d_model % num_heads == 0

            self.d_model = d_model
            self.num_heads = num_heads
            self.d_k = d_model // num_heads
            self.d_v = self.d_k

            self.q_proj = Linear(d_model, d_model)
            self.k_proj = Linear(d_model, d_model)
            self.v_proj = Linear(d_model, d_model)
            self.out_proj = Linear(d_model, d_model)

            self.rope = rope

        def forward(self, x: torch.Tensor, token_positions: torch.Tensor) -> torch.Tensor:
            batch_size, seq_len, _ = x.shape

            q = self.q_proj(x)
            k = self.k_proj(x)
            v = self.v_proj(x)

            # Reshape: (batch_size, seq_len, num_heads, d_k) -> (batch, num_heads, seq_len, d_k)
            def split_heads(t):
                return t.view(batch_size, seq_len, self.num_heads, self.d_k).transpose(1, 2)

            q = split_heads(q)
            k = split_heads(k)
            v = split_heads(v)

            # Apply RoPE
            q = self.rope(q, token_positions)
            k = self.rope(k, token_positions)

            # Create casual mask
            casual_mask = torch.triu(torch.ones(seq_len, seq_len))

            # Compute scaled dot-product attention
            attn_output = scaled_dot_product_attention(q, k, v, mask=casual_mask)

            # Merge_heads: (batch, num_heads, seq_len, d_k) -> (batch, seq_len, d_k)
            attn_output = torch.einsum('bnld-> bld', attn_output).reshape(batch_size, seq_len, self.d_model)

            return self.out_proj(attn_output)

    # RMS norm
    class RMSNorm(nn.Module):
        def __init__(self, d_model: int, eps: float = 1e-5, device=None, dtype=None):
            super.__init__()
            self.eps = eps

            # Learnable scale parameter
            self.weight = nn.Parameter(torch.ones(d_model, device=device, dtype=dtype))

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            in_dtype = x.dtype
            x = x.to(dtype=torch.float32)

            rms = torch.sqrt(torch.sum(x * x, dim=-1, keepdim=True) + self.eps)

            normed = x / rms

            result = torch.einsum('bsd, d -> bsd', normed, self.weight)
            return result.to(dtype=in_dtype)

    # Feed forward
    class SwiGLUFeedForward(nn.Module):
        def __init__(self, d_model: int, device=None, dtype=None):
            super.__init__()

            d_ff_raw = d_model * 8 / 3

            d_ff = int(math.ceil(d_ff_raw / 64) * 64)

            self.w1 = nn.Parameter(torch.empty(d_model, 2 * d_ff, device=device, dtype=dtype))
            self.b1 = nn.Parameter(torch.zero(2 * d_ff, device=device, dtype=dtype))

            self.w2 = nn.Parameter(torch.empty(d_ff, d_model, device=device, dtype=dtype))
            self.b2 = nn.Parameter(torch.zeros(d_model, device=device, dtype=dtype))

            nn.init.trunc_normal_(self.w1)
            nn.init.trunc_normal_(self.w2)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            x_proj = torch.einsum("bsd, dk -> bsk", x, self.w1) + self.b1

            value, gate = x_proj.chunk(2, dim=1)

            x_act = value * torch.nn.functional.relu(gate)

            out = torch.einsum("bsd, dk -> bsk", x_act, self.w2) + self.b2
            return out

    class transformer_block(nn.Module):
        def __init__(self, d_model: int, num_heads: int, d_ff: int):
            super.__init__()
            self.norm1 = RMSNorm(d_model, eps=1e-5)
            self.norm2 = RMSNorm(d_model, eps=1e-5)

            self.mha = MultiHeadSelfAttention(d_model, num_heads, rope=self)
            self.ff = SwiGLUFeedForward(d_model, device=None, dtype=None)

        def forward(self, x: torch.Tensor, token_positions: torch.tensor) -> torch.Tensor:
            # Sublayer 1: MHA with residual
            x = x + self.mha(self.norm1(x), token_positions)

            # Sublayer 2: FF with residual
            x = x + self.ff(self.norm2(x))

            return x

    raise NotImplementedError


def run_transformer_lm(
    vocab_size: int,
    context_length: int,
    d_model: int,
    num_layers: int,
    num_heads: int,
    d_ff: int,
    rope_theta: float,
    weights: dict[str, Tensor],
    in_indices: Int[Tensor, " batch_size sequence_length"],
) -> Float[Tensor, " batch_size sequence_length vocab_size"]:
    """Given the weights of a Transformer language model and input indices,
    return the output of running a forward pass on the input indices.

    This function should use RoPE.

    Args:
        vocab_size (int): The number of unique items in the output vocabulary to be predicted.
        context_length (int): The maximum number of tokens to process at once.
        d_model (int): The dimensionality of the model embeddings and sublayer outputs.
        num_layers (int): The number of Transformer layers to use.
        num_heads (int): Number of heads to use in multi-headed attention. `d_model` must be
            evenly divisible by `num_heads`.
        d_ff (int): Dimensionality of the feed-forward inner layer (section 3.3).
        rope_theta (float): The RoPE $\Theta$ parameter.
        weights (dict[str, Tensor]): 
            State dict of our reference implementation. {num_layers} refers to an
            integer between `0` and `num_layers - 1` (the layer index).
            The keys of this dictionary are:
            - `token_embeddings.weight`
                Token embedding matrix. Shape is (vocab_size, d_model).
            - `layers.{num_layers}.attn.q_proj.weight`
                The query projections for all `num_heads` attention heads.
                Shape is (num_heads * (d_model / num_heads), d_model).
                The rows are ordered by matrices of shape (num_heads, d_k),
                so `attn.q_proj.weight == torch.cat([q_heads.0.weight, ..., q_heads.N.weight], dim=0)`.
            - `layers.{num_layers}.attn.k_proj.weight`
                The key projections for all `num_heads` attention heads.
                Shape is (num_heads * (d_model / num_heads), d_model).
                The rows are ordered by matrices of shape (num_heads, d_k),
                so `attn.k_proj.weight == torch.cat([k_heads.0.weight, ..., k_heads.N.weight], dim=0)`.
            - `layers.{num_layers}.attn.v_proj.weight`
                The value projections for all `num_heads` attention heads.
                Shape is (num_heads * (d_model / num_heads), d_model).
                The rows are ordered by matrices of shape (num_heads, d_v),
                so `attn.v_proj.weight == torch.cat([v_heads.0.weight, ..., v_heads.N.weight], dim=0)`.
            - `layers.{num_layers}.attn.output_proj.weight`
                Weight of the multi-head self-attention output projection
                Shape is ((d_model / num_heads) * num_heads, d_model).
            - `layers.{num_layers}.ln1.weight`
                Weights of affine transform for the first RMSNorm
                applied in the transformer block.
                Shape is (d_model,).
            - `layers.{num_layers}.ffn.w1.weight`
                Weight of the first linear transformation in the FFN.
                Shape is (d_model, d_ff).
            - `layers.{num_layers}.ffn.w2.weight`
                Weight of the second linear transformation in the FFN.
                Shape is (d_ff, d_model).
            - `layers.{num_layers}.ffn.w3.weight`
                Weight of the third linear transformation in the FFN.
                Shape is (d_model, d_ff).
            - `layers.{num_layers}.ln2.weight`
                Weights of affine transform for the second RMSNorm
                applied in the transformer block.
                Shape is (d_model,).
            - `ln_final.weight`
                Weights of affine transform for RMSNorm applied to the output of the final transformer block.
                Shape is (d_model, ).
            - `lm_head.weight`
                Weights of the language model output embedding.
                Shape is (vocab_size, d_model).
        in_indices (Int[Tensor, "batch_size sequence_length"]) Tensor with input indices to run the language model on. Shape is (batch_size, sequence_length), where
            `sequence_length` is at most `context_length`.

    Returns:
        Float[Tensor, "batch_size sequence_length vocab_size"]: Tensor with the predicted unnormalized
        next-word distribution for each token.
    """
    import torch
    from torch import nn, optim
    import math

    # Multi head self attention
    def softmax(x: torch.Tensor, dim: int) -> torch.Tensor:
        x_max = torch.amax(x, dim, keepdim=True)
        x_stable = x - x_max

        exp_x = torch.exp(x_stable)
        sum_exp = torch.sum(exp_x, dim, keepdim=True)

        return exp_x / sum_exp

    class Linear(nn.Module):
        def __init__(self, in_features, out_features, device=None, dtype=None):
            super.__init__()

            self.W = nn.Parameter(
                torch.empty((out_features, in_features), device=device, dtype=dtype))
            torch.nn.init.trunc_normal_(self.W.data, a=-3.0, b=3.0)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return torch.einsum('bi, oi -> bi', x, self.W)

    def scaled_dot_product_attention(q, k, v, mask=None):
        """
        :param q: (..., seq_len_q, d_k)
        :param k: (..., seq_len_k, d_k)
        :param v: (..., seq_len_v, d_v)
        :param mask: optional (..., seq_len_q, seq_len_k) of bool
        :return: output (..., seq_len_q, d_v)
        """

        d_k = q.size(-1)

        scores = torch.einsum('...ik, ...jk -> ...ij', q, k) / math.sqrt(d_k)

        if mask is not None:
            scores = scores.masked_fill(~mask, float('-inf'))

        attn_weights = softmax(scores, dim=-1)

        output = torch.einsum('...ik, ...jk -> ...ij', attn_weights, v)

        return output

    class MultiHeadSelfAttention(nn.Module):
        def __init__(self, d_model: int, num_heads: int, rope: nn.Module):
            super.__init__()
            assert d_model % num_heads == 0

            self.d_model = d_model
            self.num_heads = num_heads
            self.d_k = d_model // num_heads
            self.d_v = self.d_k

            self.q_proj = Linear(d_model, d_model)
            self.k_proj = Linear(d_model, d_model)
            self.v_proj = Linear(d_model, d_model)
            self.out_proj = Linear(d_model, d_model)

            self.rope = rope

        def forward(self, x: torch.Tensor, token_positions: torch.Tensor) -> torch.Tensor:
            batch_size, seq_len, _ = x.shape

            q = self.q_proj(x)
            k = self.k_proj(x)
            v = self.v_proj(x)

            # Reshape: (batch_size, seq_len, num_heads, d_k) -> (batch, num_heads, seq_len, d_k)
            def split_heads(t):
                return t.view(batch_size, seq_len, self.num_heads, self.d_k).transpose(1, 2)

            q = split_heads(q)
            k = split_heads(k)
            v = split_heads(v)

            # Apply RoPE
            q = self.rope(q, token_positions)
            k = self.rope(k, token_positions)

            # Create casual mask
            casual_mask = torch.triu(torch.ones(seq_len, seq_len))

            # Compute scaled dot-product attention
            attn_output = scaled_dot_product_attention(q, k, v, mask=casual_mask)

            # Merge_heads: (batch, num_heads, seq_len, d_k) -> (batch, seq_len, d_k)
            attn_output = torch.einsum('bnld-> bld', attn_output).reshape(batch_size, seq_len, self.d_model)

            return self.out_proj(attn_output)

    # RMS norm
    class RMSNorm(nn.Module):
        def __init__(self, d_model: int, eps: float = 1e-5, device=None, dtype=None):
            super.__init__()
            self.eps = eps

            # Learnable scale parameter
            self.weight = nn.Parameter(torch.ones(d_model, device=device, dtype=dtype))

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            in_dtype = x.dtype
            x = x.to(dtype=torch.float32)

            rms = torch.sqrt(torch.sum(x * x, dim=-1, keepdim=True) + self.eps)

            normed = x / rms

            result = torch.einsum('bsd, d -> bsd', normed, self.weight)
            return result.to(dtype=in_dtype)

    # Feed forward
    class SwiGLUFeedForward(nn.Module):
        def __init__(self, d_model: int, device=None, dtype=None):
            super.__init__()

            d_ff_raw = d_model * 8 / 3

            d_ff = int(math.ceil(d_ff_raw / 64) * 64)

            self.w1 = nn.Parameter(torch.empty(d_model, 2 * d_ff, device=device, dtype=dtype))
            self.b1 = nn.Parameter(torch.zero(2 * d_ff, device=device, dtype=dtype))

            self.w2 = nn.Parameter(torch.empty(d_ff, d_model, device=device, dtype=dtype))
            self.b2 = nn.Parameter(torch.zeros(d_model, device=device, dtype=dtype))

            nn.init.trunc_normal_(self.w1)
            nn.init.trunc_normal_(self.w2)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            x_proj = torch.einsum("bsd, dk -> bsk", x, self.w1) + self.b1

            value, gate = x_proj.chunk(2, dim=1)

            x_act = value * torch.nn.functional.relu(gate)

            out = torch.einsum("bsd, dk -> bsk", x_act, self.w2) + self.b2
            return out

    class Transformer_block(nn.Module):
        def __init__(self, d_model: int, num_heads: int, d_ff: int):
            super.__init__()
            self.norm1 = RMSNorm(d_model, eps=1e-5)
            self.norm2 = RMSNorm(d_model, eps=1e-5)

            self.mha = MultiHeadSelfAttention(d_model, num_heads, rope=self)
            self.ff = SwiGLUFeedForward(d_model, device=None, dtype=None)

        def forward(self, x: torch.Tensor, token_positions: torch.tensor) -> torch.Tensor:
            # Sublayer 1: MHA with residual
            x = x + self.mha(self.norm1(x), token_positions)

            # Sublayer 2: FF with residual
            x = x + self.ff(self.norm2(x))

            return x

    # Embedding
    class Embedding(nn.Module):
        def __init__(self, num_embeddings, embedding_dim, device=None, dtype=None):
            super().__init__()

            self.embedding = nn.Parameter(torch.empty((num_embeddings, embedding_dim), device=device, dtype=dtype))

            torch.nn.init.trunc_normal_(self.W.data, a=-3.0, b=3.0)

        def forward(self, token_ids: torch.Tensor) -> torch.Tensor:
            return self.embedding[token_ids]

    class TransformerLM(nn.Module):
        def __init__(self,
                     vocab_size: int,
                     context_length: int,
                     num_layers: int,
                     d_model: int,
                     num_heads: int,
                     d_ff: int,
                     rope: nn.Module
                     ):
            super().__init__()
            self.embedding = Embedding(vocab_size, d_model)
            self.context_length = context_length
            self.num_layers = num_layers

            self.blocks = nn.ModuleList([
                Transformer_block(d_model, num_heads, d_ff)
                for _ in range(num_layers)
            ]
            )

            self.final_norm = RMSNorm(d_model, eps=1e-5)
            self.lm.head = Linear(d_model, vocab_size)

        def forward(self, token_ids: torch.Tensor) -> torch.Tensor:
            """
            :param token_ids: (batch, seq_len)
            :return: (batch, seq_len, vocab_size)
            """

            batch_size, seq_len, _ = token_ids.shape

            # Embedding
            x = self.embedding(token_ids)

            # Positional information will be added via RoPE inside attention blocks
            token_positions = torch.arange(seq_len, device=token_ids.device).unsqueeze(0)  # (1, seq_len)

            # Transformer blocks
            for block in self.blocks:
                x = block(x, token_positions)

            # Norm + add to vocab
            x = self.final_norm(x)
            logits = self.lm.head(x)  # (batch, seq_len, vocab_size)

            return logits

    raise NotImplementedError


def run_rmsnorm(
    d_model: int,
    eps: float,
    weights: Float[Tensor, " d_model"],
    in_features: Float[Tensor, " ... d_model"],
) -> Float[Tensor, " ... d_model"]:
    """Given the weights of a RMSNorm affine transform,
    return the output of running RMSNorm on the input features.

    Args:
        d_model (int): The dimensionality of the RMSNorm input.
        eps: (float): A value added to the denominator for numerical stability.
        weights (Float[Tensor, "d_model"]): RMSNorm weights.
        in_features (Float[Tensor, "... d_model"]): Input features to run RMSNorm on. Can have arbitrary leading
            dimensions.

    Returns:
        Float[Tensor,"... d_model"]: Tensor of with the same shape as `in_features` with the output of running
        RMSNorm of the `in_features`.
    """
    import torch
    from torch import nn

    class RMSNorm(nn.Module):
        def __init__(self, d_model: int, eps: float = 1e-5, device=None, dtype=None):
            super.__init__()
            self.eps = eps

            # Learnable scale parameter
            self.weight = nn.Parameter(torch.ones(d_model, device=device, dtype=dtype))

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            in_dtype = x.dtype
            x = x.to(dtype=torch.float32)

            rms = torch.sqrt(torch.sum(x * x, dim=-1, keepdim=True) + self.eps)

            normed = x / rms

            result = torch.einsum('bsd, d -> bsd', normed, self.weight)
            return result.to(dtype=in_dtype)

    raise NotImplementedError


def run_silu(in_features: Float[Tensor, " ..."]) -> Float[Tensor, " ..."]:
    """Given a tensor of inputs, return the output of applying SiLU
    to each element.

    Args:
        in_features(Float[Tensor, "..."]): Input features to run SiLU on. Shape is arbitrary.

    Returns:
        Float[Tensor,"..."]: of with the same shape as `in_features` with the output of applying
        SiLU to each element.
    """
    import torch
    from torch import nn
    import math

    class SwiGLUFeedForward(nn.Module):
        def __init__(self, d_model: int, device=None, dtype=None):
            super.__init__()

            d_ff_raw = d_model * 8 / 3

            d_ff = int(math.ceil(d_ff_raw / 64) * 64)

            self.w1 = nn.Parameter(torch.empty(d_model, 2 * d_ff, device=device, dtype=dtype))
            self.b1 = nn.Parameter(torch.zero(2 * d_ff, device=device, dtype=dtype))

            self.w2 = nn.Parameter(torch.empty(d_ff, d_model, device=device, dtype=dtype))
            self.b2 = nn.Parameter(torch.zeros(d_model, device=device, dtype=dtype))

            nn.init.trunc_normal_(self.w1)
            nn.init.trunc_normal_(self.w2)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            x_proj = torch.einsum("bsd, dk -> bsk", x, self.w1) + self.b1

            value, gate = x_proj.chunk(2, dim=1)

            x_act = value * torch.nn.functional.relu(gate)

            out = torch.einsum("bsd, dk -> bsk", x_act, self.w2) + self.b2
            return out

    raise NotImplementedError


def run_get_batch(
    dataset: npt.NDArray, batch_size: int, context_length: int, device: str
) -> tuple[torch.Tensor, torch.Tensor]:
    """
    Given a dataset (a 1D numpy array of integers) and a desired batch size and
    context length, sample language modeling input sequences and their corresponding
    labels from the dataset.

    Args:
        dataset (np.array): 1D numpy array of integer token IDs in the dataset.
        batch_size (int): Desired batch size to sample.
        context_length (int): Desired context length of each sampled example.
        device (str): PyTorch device string (e.g., 'cpu' or 'cuda:0') indicating the device
            to place the sampled input sequences and labels on.

    Returns:
        Tuple of torch.LongTensors of shape (batch_size, context_length). The first tuple item
        is the sampled input sequences, and the second tuple item is the corresponding
        language modeling labels.
    """
    import torch
    import numpy as np
    import numpy.typing as npt

    def run_get_batch(dataset: npt.NDArray, batch_size: int, context_length: int, device: str) -> tuple[
        torch.Tensor, torch.Tensor]:
        # Sample random starting indices
        max_start = len(dataset) - context_length - 1
        starts = np.random.randint(0, max_start, size=batch_size)

        # Create inputs and targets
        inputs = np.stack(dataset[i: i + context_length] for i in starts)
        targets = np.stack(dataset[i + 1: i + 1 + context_length] for i in starts)

        # Converts to torch tensor
        inputs_tensor = torch.tensor(inputs, dtype=torch.long, device=device)
        targets_tensor = torch.tensor(targets, dtype=torch.long, device=device)

        return inputs_tensor, targets_tensor

    raise NotImplementedError


def run_softmax(in_features: Float[Tensor, " ..."], dim: int) -> Float[Tensor, " ..."]:
    """
    Given a tensor of inputs, return the output of softmaxing the given `dim`
    of the input.

    Args:
        in_features (Float[Tensor, "..."]): Input features to softmax. Shape is arbitrary.
        dim (int): Dimension of the `in_features` to apply softmax to.

    Returns:
        Float[Tensor, "..."]: Tensor of with the same shape as `in_features` with the output of
        softmax normalizing the specified `dim`.
    """
    import torch
    from torch import nn

    def softmax(x: torch.Tensor, dim: int) -> torch.Tensor:
        x_max = torch.amax(x, dim, keepdim=True)
        x_stable = x - x_max

        exp_x = torch.exp(x_stable)
        sum_exp = torch.sum(exp_x, dim, keepdim=True)

        return exp_x / sum_exp

    raise NotImplementedError


def run_cross_entropy(inputs: Float[Tensor, " batch_size vocab_size"], targets: Int[Tensor, " batch_size"]) -> Float[Tensor, ""]:
    """Given a tensor of inputs and targets, compute the average cross-entropy
    loss across examples.

    Args:
        inputs (Float[Tensor, "batch_size vocab_size"]): inputs[i][j] is the
            unnormalized logit of jth class for the ith example.
        targets (Int[Tensor, "batch_size"]): Tensor of shape (batch_size,) with the index of the correct class.
            Each value must be between 0 and `num_classes - 1`.

    Returns:
        Float[Tensor, ""]: The average cross-entropy loss across examples.
    """
    import torch
    from numpy.ma.core import soften_mask
    from torch import nn

    def cross_entropy_loss(logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        """
        Computes the cross entropy between logits and targets.
        """
        max_logits = logits.max(dim=-1, keepdim=True)[0]
        logits_stable = logits - max_logits
        exp_logits = torch.exp(logits_stable)
        softmax_denominator = exp_logits.sum(dim=-1, keepdim=True)

        softmax_probs = exp_logits / softmax_denominator

        # Gather probabilities of the correct tokens
        correct_token_probs = softmax_probs.gather(-1, targets.unsqueeze(-1)).squeeze(-1)

        # Cross entropy loss
        loss = -torch.log(correct_token_probs)

        return loss.mean()
    raise NotImplementedError


def run_gradient_clipping(parameters: Iterable[torch.nn.Parameter], max_l2_norm: float) -> None:
    """Given a set of parameters, clip their combined gradients to have l2 norm at most max_l2_norm.

    Args:
        parameters (Iterable[torch.nn.Parameter]): collection of trainable parameters.
        max_l2_norm (float): a positive value containing the maximum l2-norm.

    The gradients of the parameters (parameter.grad) should be modified in-place.
    """
    import torch
    from torch import nn

    def clip_gradients(params, max_norm, eps=1e-6):
        total_norm = 0
        for p in params:
            if p.grad is not None:
                grad = p.grad.data
                total_norm += torch.sum(grad ** 2).item()
        total_norm = torch.sqrt(total_norm + eps)

        if total_norm > max_norm:
            scale = max_norm / (total_norm + eps)
            for p in params:
                if p.grad is not None:
                    p.grad.data.mul_(scale)

    raise NotImplementedError


def get_adamw_cls() -> type[torch.optim.Optimizer]:
    """
    Returns a torch.optim.Optimizer that implements AdamW.
    """
    import torch
    from torch.optim import Optimizer
    import math

    class AdamW(Optimizer):
        def __init__(self, params, lr=1e-3, betas=(0.9, 0.999), eps=1e-8, weight_decay=0):
            defaults = dict(lr=lr, betas=betas, eps=eps, weight_decay=weight_decay)
            super().__init__(params, defaults)

        def step(self, closure=None):
            loss = closure() if closure is not None else None

            for group in self.param_groups:
                for param in group['params']:
                    if param.grad is None:
                        continue
                    grad = param.grad.data
                    if grad.is_sparse:
                        raise RuntimeError('Adam does not support sparse gradients')

                    state = self.state[param]

                    # Step count
                    if 'step' not in state:
                        state['step'] = 0
                        state['exp_avg'] = torch.zeros_like(param.data)  # m
                        state['exp_avg_sq'] = torch.zeros_like(param.data)  # v

                    state['step'] += 1
                    step = state['step']
                    m, v = state['exp_avg'], state['exp_avg_sq']

                    beta1, beta2 = group['betas']
                    eps = group['eps']
                    lr = group['lr']
                    weight_decay = group['weight_decay']

                    # Update first moment estimate
                    m.mul_(beta1).add_(1 - beta1, grad)

                    # Update second moment estimate
                    v.mul_(beta2).addcmul(1 - beta2, grad, grad)

                    # Compute bias correction
                    bias_correction1 = 1 - beta1 ** step
                    bias_correction2 = 1 - beta2 ** step

                    step_size = lr * math.sqrt(bias_correction2) / bias_correction1

                    # Parameter update
                    denom = v.sqrt().add_(eps)
                    param.data.addcdiv_(m, denom, value=-step_size)

                    # Apply weight decay
                    if weight_decay != 0:
                        param.data.add_(param.data, alpha=-lr * weight_decay)

            return loss

    raise NotImplementedError


def run_get_lr_cosine_schedule(
    it: int,
    max_learning_rate: float,
    min_learning_rate: float,
    warmup_iters: int,
    cosine_cycle_iters: int,
):
    """
    Given the parameters of a cosine learning rate decay schedule (with linear
    warmup) and an iteration number, return the learning rate at the given
    iteration under the specified schedule.

    Args:
        it (int): Iteration number to get learning rate for.
        max_learning_rate (float): alpha_max, the maximum learning rate for
            cosine learning rate schedule (with warmup).
        min_learning_rate (float): alpha_min, the minimum / final learning rate for
            the cosine learning rate schedule (with warmup).
        warmup_iters (int): T_w, the number of iterations to linearly warm-up
            the learning rate.
        cosine_cycle_iters (int): T_c, the number of cosine annealing iterations.

    Returns:
        Learning rate at the given iteration under the specified schedule.
    """
    import torch
    from torch import nn
    import math

    def cosine_learning_rate_schedule(t, alpha_max, alpha_min, T_w, T_c):
        if t < T_w:
            alpha_t = t / T_w * alpha_max
        elif T_w <= t <= T_c:
            alpha_t = alpha_min + 1 / 2 * (1 + math.cos((t - T_w) / (T_c - T_w)) * math.pi) * (alpha_max - alpha_min)
        else:
            alpha_t = alpha_min
        return alpha_t
    raise NotImplementedError


def run_save_checkpoint(
    model: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    iteration: int,
    out: str | os.PathLike | BinaryIO | IO[bytes],
):
    """
    Given a model, optimizer, and an iteration number, serialize them to disk.

    Args:
        model (torch.nn.Module): Serialize the state of this model.
        optimizer (torch.optim.Optimizer): Serialize the state of this optimizer.
        iteration (int): Serialize this value, which represents the number of training iterations
            we've completed.
        out (str | os.PathLike | BinaryIO | IO[bytes]): Path or file-like object to serialize the model, optimizer, and iteration to.
    """
    import torch
    from torch import nn
    import os
    import typing

    def save_checkpoint(model: torch.nn.Module, optimizer: torch.optim.Optimizer, iteration: int,
                        out: str | os.PathLike | typing.BinaryIO | typing.IO[bytes]):
        checkpoint = {
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'iteration': iteration,
        }
        return torch.save(checkpoint, out)
    raise NotImplementedError


def run_load_checkpoint(
    src: str | os.PathLike | BinaryIO | IO[bytes],
    model: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
):
    """
    Given a serialized checkpoint (path or file-like object), restore the
    serialized state to the given model and optimizer.
    Return the number of iterations that we previously serialized in
    the checkpoint.

    Args:
        src (str | os.PathLike | BinaryIO | IO[bytes]): Path or file-like object to serialized checkpoint.
        model (torch.nn.Module): Restore the state of this model.
        optimizer (torch.optim.Optimizer): Restore the state of this optimizer.
    Returns:
        int: the previously-serialized number of iterations.
    """
    import torch
    from torch import nn
    import os
    import typing

    def load_checkpoint(src: str | os.PathLike | typing.BinaryIO | typing.IO[bytes], model: torch.nn.Module,
                        optimizer: torch.optim.Optimizer):
        checkpoint = torch.load(src)
        model.load_state_dict(checkpoint['model_state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        iteration = checkpoint['iteration']
        return model, optimizer, iteration

    raise NotImplementedError


def get_tokenizer(
    vocab: dict[int, bytes],
    merges: list[tuple[bytes, bytes]],
    special_tokens: list[str] | None = None,
) -> Any:
    """Given a vocabulary, a list of merges, and a list of special tokens,
    return a BPE tokenizer that uses the provided vocab, merges, and special tokens.

    Args:
        vocab (dict[int, bytes]): The tokenizer vocabulary, a mapping from int (token ID in the vocabulary)
            to bytes (token bytes)
        merges (list[tuple[bytes, bytes]]): BPE merges. Each list item is a tuple of bytes (<token1>, <token2>),
            representing that <token1> was merged with <token2>.
            Merges are ordered by order of creation.
        special_tokens (list[str] | None): A list of string special tokens for the tokenizer. These strings will never
            be split into multiple tokens, and will always be kept as a single token.

    Returns:
        A BPE tokenizer that uses the provided vocab, merges, and special tokens.
    """
    raise NotImplementedError


def run_train_bpe(
    input_path: str | os.PathLike,
    vocab_size: int,
    special_tokens: list[str],
    **kwargs,
) -> tuple[dict[int, bytes], list[tuple[bytes, bytes]]]:
    """Given the path to an input corpus, run train a BPE tokenizer and
    output its vocabulary and merges.

    Args:
        input_path (str | os.PathLike): Path to BPE tokenizer training data.
        vocab_size (int): Total number of items in the tokenizer's vocabulary (including special tokens).
        special_tokens (list[str]): A list of string special tokens to be added to the tokenizer vocabulary.
            These strings will never be split into multiple tokens, and will always be
            kept as a single token. If these special tokens occur in the `input_path`,
            they are treated as any other string.

    Returns:
        tuple[dict[int, bytes], list[tuple[bytes, bytes]]]:
            vocab:
                The trained tokenizer vocabulary, a mapping from int (token ID in the vocabulary)
                to bytes (token bytes)
            merges:
                BPE merges. Each list item is a tuple of bytes (<token1>, <token2>),
                representing that <token1> was merged with <token2>.
                Merges are ordered by order of creation.
    """
    raise NotImplementedError
