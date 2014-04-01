#lang s-exp rosette
(require "util.rkt")
(provide (all-defined-out))

(define (ab_s a b)
(define op #f)
(if (< b 0)(set! op +)
(set! op -)
)
( op a b )
)
