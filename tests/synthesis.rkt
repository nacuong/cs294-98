#lang s-exp rosette

(define-symbolic i0 i1 number?)
(configure [bitwidth 32])

;; no need to generate
(define-syntax-rule (either c a ...)
  (choose c (list a ...)))

(define (choose c lst)
  (list-ref lst c))

;; AllNum - change 10 & -10 to ub and lb
(define (n? n)
  (assert (and (< n 10) (>= n -10)))
  n)

;; For AllVarNum - change 10 & -10 to ub and lb
(define (n?? nn)
  (assert (and (< nn 10) (>= nn -10)))
  nn)

(define (f x y) (+ x y 3))

(define (g x y)
  ;; AllVar - body depends on all variables in the function
  (define (v? v)
    (cond
      [(= v 0) x]
      [(= v 1) y]))

  ;; AllVarNum - body depends on all variables in the function
  (define (v?? vv)
    (cond
      [(= vv 0) x]
      [(= vv 1) y]))
  
  ;; AllVarNum
  (define (?? vn v n)
    (if vn (v?? v) (n?? n)))
  
  ;; AllVarNum - variables depend on allvarnum holes
  (define-symbolic _vn0 _vn1 _vn2 _vn3 _vn4 _vn5 _vn6 _vn7 _vn8 boolean?)
  (define-symbolic _vv0 _vv1 _vv2 _vv3 _vv4 _vv5 _vv6 _vv7 _vv8 number?)
  (define-symbolic _nn0 _nn1 _nn2 _nn3 _nn4 _nn5 _nn6 _nn7 _nn8 number?)
  
  ;; Either - variables depend on either holes
  (define-symbolic _c0 number?)
    
  (either _c0
          (+ (?? _vn0 _vv0 _nn0) (?? _vn1 _vv1 _nn1) (?? _vn2 _vv2 _nn2)) 
          (- (?? _vn3 _vv3 _nn3) (?? _vn4 _vv4 _nn4) (?? _vn5 _vv5 _nn5)) 
          (* (?? _vn6 _vv6 _nn6) (?? _vn7 _vv7 _nn7) (?? _vn8 _vv8 _nn8))))

  ;; Not working yet. Emina needs to support macro expansion.
  ;; ((either + - *) (??) (??) (??)))

  ;(for/all ([o (either + - *)]) (o (??) (??) (??))))

(define model
(synthesize
  #:forall (list i0 i1)
  #:assume (assert (and (< i0 10000) (> i0 -10000) (< i1 10000) (> i1 -10000)))
  #:guarantee (assert (equal? (f i0 i1) (g i0 i1)))))

(pretty-display (solution->list model))
(define solution (solution->list model))
(for-each (lambda (sol)
	(define val (cdr sol))
	(define sym (sym-name (car sol)))
	(define symtype (syntax->datum (car sym)))
	(define symid (cdr sym))
	(printf "~a:~a:~a\n" symtype symid val))
	 solution)