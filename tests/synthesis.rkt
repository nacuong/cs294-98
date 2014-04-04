#lang s-exp rosette

(define-symbolic i0 i1 number?)
(configure [bitwidth 32])

(define (n?)
  (define-symbolic* num number?)
  num)

(define-syntax-rule (either a ...)
  (choose (list a ...)))

(define (choose lst)
  (define-symbolic* choice number?)
  (list-ref lst choice))

(define (f x y) (+ x y 3))

(define (g x y)
  (define (v?)
    (define-symbolic* var number?)
    (cond
      [(= var 0) x]
      [(= var 1) y]))
  
  (define (??)
    (define-symbolic* is-var boolean?)
    (if is-var (v?) (n?)))
    
  (either (+ (??) (??) (??)) (- (??) (??) (??)) (* (??) (??) (??))))

(define model
(synthesize
  #:forall (list i0 i1)
  #:assume (assert (and (< i0 10000) (> i0 -10000) (< i1 10000) (> i1 -10000)))
  #:guarantee (assert (eq? (f i0 i1) (g i0 i1)))))