#lang s-exp rosette

(require rosette/lang/debug)
(require (only-in rosette [+ sym/+]))

(provide (all-defined-out))

(define-syntax-rule (while cond s0 ...)
  (let ([count 0]
        [bound (configured loop-bound)])
    (for ([i (in-range bound)])
      (when cond
        s0 ...
        (set! count (add1 count))))
    (assert (< count bound))))

(define-syntax-rule (bounded def (id arg ...) expr ...)
  (define (id arg ...)
    (define bound (configured loop-bound))
    (def (id arg ...)
      (if (protect (> bound 0))
          (begin 
            (set! bound (protect (sub1 bound)))
            (define val (let () expr ...))
            (set! bound (protect (add1 bound)))
            val)
          (assert #f)))
    (id arg ...)))

(define-syntax-rule (define/bounded (id arg ...) expr ...)
  (bounded define (id arg ...) expr ...))

(define-syntax-rule (define/debug/bounded (id arg ...) expr ...)
  (bounded define/debug (id arg ...) expr ...))

(define-syntax max
  (syntax-rules ()
    ((max a b)
     (if (> a b) a b))
    ((max a x ...)
     (let ([b (max x ...)])
       (if (> a b) a b)))))

(define-syntax min
  (syntax-rules ()
    ((min a b)
     (if (< a b) a b))
    ((min a x ...)
     (let ([b (min x ...)])
       (if (< a b) a b)))))

(define-syntax-rule (list-set l i x)
  (let ([vec (list->vector l)])
    (vector-set! vec i x)
    (vector->list vec)))

(define-syntax-rule (len l) 
  (if (list? l)
      (length l)
      (assert #f)))

(define-syntax range
  (syntax-rules ()
    ((range y) (range 0 y))
    ((range x y) (range-func x y))
    ))

(define/bounded (range-func l u)
  (if (< l u)
      (cons l (range-func (add1 l) u))
      (list)))

(define-syntax-rule (+ x y ...)
  (if (list? x)
      (append x y ...)
      (sym/+ x y ...)))
              
(define/bounded (expt b p)
  (if (= p 0)
      1
      (* b (expt b (sub1 p)))))