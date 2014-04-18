#lang s-exp rosette

(define-symbolic i0 i1 number?)
(configure [bitwidth 32])

;; no need to generate
(define-syntax-rule (either a ...)
  (choose (list a ...)))

(define (choose lst)
  (define-symbolic* choice number?)
  (list-ref lst choice))

;; AllNum
(define (n?)
  (define-symbolic* n number?)
  (assert (and (< n 10) (>= n -10)))
  n)

;; For AllVarNum
(define (n??)
  (define-symbolic* nn number?)
  (assert (and (< nn 10) (>= nn -10)))
  nn)

(define (f x y) (+ x y 3))

(define (g x y)
  ;; AllVar
  (define (v?)
    (define-symbolic* v number?)
    (cond
      [(= v 0) x]
      [(= v 1) y]))

  ;; For AllVarNum
  (define (v??)
    (define-symbolic* vv number?)
    (cond
      [(= vv 0) x]
      [(= vv 1) y]))
  
  ;; AllVarNum
  (define (??)
    (define-symbolic* is-var boolean?)
    (if is-var (v??) (n??)))
    
  (either (+ (??) (??) (??)) 
          (- (??) (??) (??)) 
          (* (??) (??) (??))))

  ;; Not working yet. Emina needs to support macro expansion.
  ;; ((either + - *) (??) (??) (??)))

  ;(for/all ([o (either + - *)]) (o (??) (??) (??))))

(define model
(synthesize
  #:forall (list i0 i1)
  ;#:assume (assert (and (= i0 1) (= i1 2)))
  #:assume (assert (and (< i0 10000) (> i0 -10000) (< i1 10000) (> i1 -10000)))
  #:guarantee (assert (eq? (f i0 i1) (g i0 i1)))))

(pretty-display (solution->list model))